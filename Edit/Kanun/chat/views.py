from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import FileResponse
from django.conf import settings
from .models import ChatUsageLog, Conversation, GeneratedImage
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import PromptTemplate
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from openai import OpenAI
import uuid
import logging
import requests
import os
from dotenv import load_dotenv

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "kanun")

# Validate environment variables
if not all([QDRANT_HOST, QDRANT_PORT, OPENAI_API_KEY, COLLECTION_NAME]):
    raise EnvironmentError("Missing required environment variables.")

# Initialize Qdrant client
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Initialize embeddings and LLM
embeddings = OpenAIEmbeddings()
model_name = "gpt-4o-mini-2024-07-18"
llm = ChatOpenAI(model=model_name, temperature=0)

# Prompt templates
custom_prompt = PromptTemplate.from_template("""Use the following pieces of context to answer the question at the end. If the similar answer is there in context answer accordingly otherwise say you dont know. Do not add information other than present on Context or Chat History but elaborate(write at least 2 paragraphs) if the it is asked.
Context:{context}
Chat History:{chat_history}
Question:{question}
Answer:""")

#custom_prompt = PromptTemplate.from_template("""Use the following pieces of context to answer the question at the end. If the similar answer is there in context answer accordingly but if similar answer not found in the given context, just say that you don't know. Do not add information other than present on Context or Chat History but elaborate if the it is asked.
#Context:{context}
#Chat History:{chat_history}
#Question:{question}
#Answer:""")

rephrase_follow_up_prompt = PromptTemplate.from_template("""Analyze the Chat History and Follow-up questions. If the follow-up question is not in context, reply with the input as it is. If it is in context, rephrase it into a standalone question also elaborate being in context if asked to.
Chat History:
{chat_history}
Follow Up Input: {input}
Standalone Question:""")

fort=None
embed=None

#error here 
def format_docs(documents):
    global fort
    """Format retrieved documents for inclusion in context."""
    #print("Formatted documents:")
    #print(documents)

    formatted_texts = []
    
    for doc in documents:
     #   print("*" * 20)
      #  print(doc)
       # print("*" * 20)

        # Extract the text field safely
        text_content = doc.payload.get('text', '[No Content]')
        formatted_texts.append(f"Content: {text_content}...")
    fort = formatted_texts
    return "\n\n".join(formatted_texts)




def format_chat_history(chat_history):
    """Format chat history into a string."""
    return "\n".join([f"{entry['role']}: {entry['message']}" for entry in chat_history])

def calculate_cost(token_usage, cost_per_1k_tokens=0.002):
    """Calculate cost based on token usage."""
    return (token_usage / 1000) * cost_per_1k_tokens

@login_required
def chat_create_view(request):
    session_id = str(uuid.uuid4())
    conversation = Conversation.objects.create(user=request.user, session_id=session_id)
    return redirect("chat", conversation_id=conversation.id)

@login_required
def chat_view(request, conversation_id):
    global embed
    conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
    chat_history = conversation.chat_history

    # Ensure 'embed' has a default value to prevent UnboundLocalError
    if embed is None:
        embed = []

    if request.method == "POST":
        query = request.POST.get("query", "").strip().lower()

        if not query or len(query.split()) < 2:
            response = "Please provide a valid question."
            ChatUsageLog.objects.create(user=request.user, query=query, response=response, token_usage=0, cost=0, model=model_name)
            chat_history.extend([{"role": "human", "message": query}, {"role": "ai", "message": response}])
            conversation.chat_history = chat_history
            conversation.save()
            return render(request, "chat/chat.html", {"chat_history": chat_history, "conversation": conversation})

        rephrased_query = query
      
        if chat_history:
            rephrase_prompt_with_query = rephrase_follow_up_prompt.format(chat_history=format_chat_history(chat_history), input=query)
            try:
                rephrased_query = llm.invoke(rephrase_prompt_with_query).content.strip()
               # print("*" * 40)
                #print("Rephrased query")
               # print(rephrased_query)
                #print("*" * 40)
                #print()
            except Exception as e:
                logger.error(f"Error in rephrasing query: {e}")

        # Retrieve documents from Qdrant
        try:
            query_embedding = embeddings.embed_query(rephrased_query)
            #print("&"*12 + "&"*12)
            #print("*"*30)
            #print('**********************query_embedding*******************')
            #print(query_embedding)
            embed=query_embedding
            print(embed)
            retrieved_docs = client.search(collection_name=COLLECTION_NAME, query_vector=query_embedding, limit=5)
           # print("*******************************retrieved Documents******************************************************")
            #print(retrieved_docs)
        except Exception as e:
            logger.error(f"Error in retrieving documents: {e}")
            retrieved_docs = []
        
       
        formatted_context = format_docs(retrieved_docs)
        print("Formateed Context ***********************"+ formatted_context)
        if not formatted_context.strip():
            response = "I couldn't find any relevant information."
            ChatUsageLog.objects.create(user=request.user, query=query, response=response, token_usage=0, cost=0, model=model_name)
            chat_history.extend([{"role": "human", "message": query}, {"role": "ai", "message": response}])
            conversation.chat_history = chat_history
            conversation.save()
            return render(request, "chat/chat.html", {"chat_history": chat_history, "conversation": conversation})

        prompt_with_context = custom_prompt.format(context=formatted_context, chat_history=format_chat_history(chat_history), question=rephrased_query)
        try:
            #print(prompt_with_context)
            llm_response = llm.invoke(prompt_with_context)
            response = llm_response.content.strip()
            #print("LLM response " + response)
            token_usage = llm_response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
        except Exception as e:
            logger.error(f"Error in LLM prediction: {e}")
            response = "Sorry, I couldn't process your query."
            token_usage = 0

        cost = calculate_cost(token_usage)
        ChatUsageLog.objects.create(user=request.user, query=query, response=response, token_usage=token_usage, cost=cost, model=model_name)
        chat_history.extend([{"role": "human", "message": query}, {"role": "ai", "message": response}])
        conversation.chat_history = chat_history
        conversation.save()
    print("##################################3")    
    print(fort)
    print("(((((((((((((((((((((((((((((((((())))))))))))))))))))))))))))))))))" )
    print(embed)
    embed_items = embed[:20] 
    return render(request, "chat/chat.html", {"chat_history": chat_history, "conversation": conversation, 'fort': fort, 'embed':embed_items})

@login_required
def chat_list_view(request):
    """List all conversations for the logged-in user."""
    conversations = Conversation.objects.filter(user=request.user)
    #print('*****************************************')
    #print('    *      *       Conversations    *   *   * ')
    #print(conversations)
    #print('*******************************************')
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
    """Generate an image using DALL·E and save it in the database and media folder."""
    image_url = None
    error_message = None
    saved_image = None

    if request.method == 'POST':
        query = request.POST.get("query", "").strip()
        if query:
            try:
                # Generate the image using the OpenAI DALL·E client
                client = OpenAI()
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=query,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                image_url = response.data[0].url  # DALL-E generated image URL

                # Download the image from the generated URL
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    image_name = f"{request.user.username}_{query.replace(' ', '_')}.png"

                    # Create the database record first
                    saved_image = GeneratedImage.objects.create(
                        user=request.user,
                        prompt=query,
                        image_url=image_url,
                    )
                    # Use Django's file storage to save the image file.
                    saved_image.image_file.save(
                        f"generated_images/{image_name}",
                        ContentFile(image_response.content)
                    )
                    saved_image.save()
                else:
                    error_message = "Error downloading image from DALL·E."
            except Exception as e:
                error_message = f"Error generating image: {e}"

    return render(request, "chat/generate_image.html", {
        'image_url': image_url,
        'saved_image': saved_image,
        'error_message': error_message
    })


@login_required
def download_image(request, image_id):
    """Download the saved image from the media folder."""
    image = get_object_or_404(GeneratedImage, id=image_id)

    # Ensure the image is saved locally
    if not image.image_file:
        return HttpResponse("Image not found", status=404)

    file_path = os.path.join(settings.MEDIA_ROOT, str(image.image_file))
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))

    return HttpResponse("Error downloading image", status=500)
