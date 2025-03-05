from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatUsageLog, Conversation
from langchain_openai import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from django.db.models import Sum, Count
import uuid
from django.contrib.auth.decorators import login_required
from uuid import uuid4
from dotenv import load_dotenv
import os
import logging
from openai import OpenAI
import requests
from django.core.files.base import ContentFile
from django.conf import settings

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")

# Initialize embeddings, LLM, and vector store
embeddings = OpenAIEmbeddings()
model_name = "gpt-4o-mini-2024-07-18"  # Example model name
llm = ChatOpenAI(model=model_name, temperature=0)
vectorstore = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
a=None

# Prompt templates
custom_prompt = PromptTemplate.from_template("""
Use the following pieces of context to answer the question at the end. If you don't know the 
answer, just say that you don't know. Write answer in two paragraphs.
Context:
{context}
Chat History:
{chat_history}
Question:
{question}
Answer:
""")

rephrase_follow_up_prompt = PromptTemplate.from_template("""\
First of all analyze the Chat History and Follow up questions.
If the follow up question is not in context just reply you don't know.
And if the follow up question is context reply accordingly. 
Chat History:
{chat_history}
Follow Up Input: {input}
Standalone Question:
""")

def format_docs(documents):
    """
    Format a list of Document objects into a string for inclusion in the context.
    Each Document object is expected to have `metadata` and `page_content` attributes.
    """
    formatted = []
    for doc in documents:
        print(doc)
        title = doc.metadata.get('title', 'Untitled')  # Access `metadata` dictionary
        content_preview = doc.page_content[:200]  # Get a preview of the document content
        formatted.append(f"Title: {title}\nContent: {content_preview}...")
    return "\n\n".join(formatted)

def format_chat_history(chat_history):
    """Format chat history into a string for inclusion in the prompt."""
    return "\n".join([f"{entry['role']}: {entry['message']}" for entry in chat_history])

@login_required
def chat_create_view(request):
    """Create a new conversation and redirect to its chat view."""
    session_id = str(uuid4())
    conversation = Conversation.objects.create(user=request.user, session_id=session_id)
    return redirect("chat", conversation_id=conversation.id)

@login_required
def chat_view(request, conversation_id):
    """View and interact with an existing conversation."""
    global a
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)

    
    # Load chat history from the database
    chat_history = conversation.chat_history
    
    if request.method == "POST":
        query = request.POST.get("query", "").strip()

        # Input validation: Check for empty or garbage input
        if not query or len(query.split()) < 2:  # Minimum word count to avoid garbage input
            response = "Please provide a valid question. I couldn't understand your input."
            ChatUsageLog.objects.create(
                user_id=request.user.id,
                query=query,
                response=response,
                token_usage=0,
                cost=0,
                model=model_name
            )
            chat_history.extend([
                {"role": "human", "message": query},
                {"role": "ai", "message": response}
            ])
            conversation.chat_history = chat_history
            conversation.save()
            return render(request, "chat/chat.html", {"chat_history": chat_history, "conversation": conversation})

        # Rephrase the question if there is chat history
        rephrased_query = query
        if chat_history:
            rephrase_prompt_with_query = rephrase_follow_up_prompt.format(
                chat_history=format_chat_history(chat_history),
                input=query
            )
            try:
                rephrased_query = llm.invoke(rephrase_prompt_with_query).content.strip()
            except Exception as e:
                logger.error(f"Error in rephrasing query: {e}")
                rephrased_query = query  # Fallback if error occurs

        # Retrieve documents using MMR
        retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"lambda_mult": 0.5, "k": 5})  # Limit results to top 5
        try:
            retrieved_docs = retriever.invoke(rephrased_query)
        except Exception as e:
            logger.error(f"Error in retrieving documents: {e}")
            retrieved_docs = []  # Fallback to empty docs if retrieval fails

        # Format the context for the LLM response
        formatted_context = format_docs(retrieved_docs)

        # Ensure the system only responds if relevant documents are found
        if not formatted_context.strip():
            response = "I couldn't find any relevant information in the database to answer your question."
            ChatUsageLog.objects.create(
                user_id=request.user.id,
                query=query,
                response=response,
                token_usage=0,
                cost=0,
                model=model_name
            )
            chat_history.extend([
                {"role": "human", "message": query},
                {"role": "ai", "message": response}
            ])
            conversation.chat_history = chat_history
            conversation.save()
            return render(request, "chat/chat.html", {"chat_history": chat_history, "conversation": conversation})

        # Generate the response ONLY based on the retrieved documents
        prompt_with_context = custom_prompt.format(
            context=formatted_context,
            chat_history=format_chat_history(chat_history),
            question=rephrased_query
        )
        try:
            a = llm.invoke(prompt_with_context)
            if a:
                response = a.content.strip()
                total_tokens = a.response_metadata.get("token_usage", {}).get("total_tokens", 0)
            else:
                response = "Sorry, no response from the model."
        except Exception as e:
            logger.error(f"Error in LLM prediction: {e}")
            response = "Sorry, I couldn't process your query at the moment."

        # Log the interaction
        token_usage = a.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        cost_per_1k_tokens = 0.002
        cost = (token_usage / 1000) * cost_per_1k_tokens
        ChatUsageLog.objects.create(
            user_id=request.user.id,
            query=query,
            response=response,
            token_usage=token_usage,
            cost=cost,
            model=model_name
        )

        # Update chat history and save to the database
        chat_history.extend([
            {"role": "human", "message": query},
            {"role": "ai", "message": response}
        ])
        conversation.chat_history = chat_history
        conversation.save()

    # Pass `a` to the template, even if it's None
    tester = {"chat_history": chat_history, "conversation": conversation, "a": a}
    return render(request, "chat/chat.html", tester)

@login_required
def chat_list_view(request):
    """List all conversations for the logged-in user."""
    conversations = Conversation.objects.filter(user=request.user)  # Respects Meta ordering
    return render(request, "chat/chat_list.html", {"conversations": conversations})

@login_required
def dashboard_view(request):
    """Dashboard to display usage statistics."""
    total_cost = ChatUsageLog.objects.aggregate(Sum('cost'))['cost__sum'] or 0
    total_tokens = ChatUsageLog.objects.aggregate(Sum('token_usage'))['token_usage__sum'] or 0
    model_usage = ChatUsageLog.objects.values('model').annotate(
        count=Count('id'),
        tokens=Sum('token_usage'),
        cost=Sum('cost')
    )
    return render(request, "dashboard/dashboard.html", {
        "total_cost": total_cost,
        "total_tokens": total_tokens,
        "model_usage": model_usage,
    })

@login_required
def generate_image(request):
    """Generate an image using DALL·E and store it in the database."""
    image_url = None
    error_message = None
    conversation = None  # To associate the image with a conversation

    if request.method == 'POST':
        query = request.POST.get("query", "").strip()
        conversation_id = request.POST.get("conversation_id")

        if query and conversation_id:
            try:
                # Initialize OpenAI client
                client = OpenAI()
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=query,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )

                # Extract image URL from OpenAI response
                image_url = response.data[0].url

                # Retrieve the image content
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    # Save image to the Conversation model
                    conversation = Conversation.objects.get(id=conversation_id)
                    image_content = ContentFile(image_response.content)

                    # Generate a unique filename
                    filename = f"{uuid.uuid4()}.png"

                    # Save the image file to the model's `ImageField`
                    conversation.generated_image.save(filename, image_content)
                    conversation.save()
                else:
                    error_message = "Failed to retrieve image from the generated URL."

            except Exception as e:
                error_message = f"Error generating image: {e}"

    return render(request, "chat/generate_image.html", {
        'image_url': image_url,
        'error_message': error_message,
        'conversation': conversation
    })