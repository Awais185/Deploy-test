from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from openai import OpenAI
from django.conf import settings
from .models import GeneratedComment, IncomingReply, JoinedGroup, WelcomeTemplate
from .serializers import (
    CheckPostResponseSerializer,
    CheckGroupResponseSerializer,
    ErrorResponseSerializer,
    GenerateCommentResponseSerializer,
    GroupURLRequestSerializer,
    IncomingMessageRequestSerializer,
    IncomingMessageResponseSerializer,
    ProcessNotificationRequestSerializer,
    ProcessNotificationResponseSerializer,
    SaveGroupResponseSerializer,
    UpdateCommentStatusRequestSerializer,
    UpdateCommentStatusResponseSerializer,
    WelcomeMessageResponseSerializer,
    PostTextRequestSerializer,
)
import re
from difflib import SequenceMatcher


def normalize_post_text(value):
    if not value:
        return ''
    text = str(value).strip().lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text.strip()


def is_similar_post(a, b):
    a_norm = normalize_post_text(a)
    b_norm = normalize_post_text(b)
    if not a_norm or not b_norm:
        return False
    if a_norm == b_norm:
        return True
    if a_norm in b_norm or b_norm in a_norm:
        return True
    return SequenceMatcher(None, a_norm, b_norm).ratio() >= 0.82


def normalize_message(value):
    if not value:
        return ''
    text = str(value).lower().strip()
    text = re.sub(r'https?\S+|www\.\S+', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def should_skip_business_message(message):
    if not message:
        return True

    text = normalize_message(message)
    if len(text) < 8:
        return True

    generic_phrases = ['hi', 'hello', 'hey', 'good morning', 'good evening', 'how are you', 'thanks']
    if any(phrase in text for phrase in generic_phrases):
        if not re.search(r'\b(web|website|shopify|seo|ai|automation|app|software|developer|design|marketing|wordpress|n8n|ecommerce|store|landing page|business|agency)\b', text):
            return True

    business_keywords = [
        'website', 'web', 'shopify', 'seo', 'digital marketing', 'marketing', 'ai', 'automation',
        'n8n', 'app', 'software', 'developer', 'designer', 'wordpress', 'landing page', 'ux', 'ui',
        'ecommerce', 'store', 'brand', 'web development', 'mobile app', 'saas', 'mvp', 'dropshipping',
        'react', 'python', 'api', 'build', 'design', 'agency', 'business website', 'online store',
        'need help', 'looking for', 'hire', 'hiring', 'need a', 'require', 'budget', 'quote', 'price'
    ]

    if not any(keyword in text for keyword in business_keywords):
        return True

    return False


client = OpenAI(
    api_key=settings.CLOUDFLARE_API_TOKEN,
    base_url=f"https://api.cloudflare.com/client/v4/accounts/{settings.CLOUDFLARE_ACCOUNT_ID}/ai/v1"
)
SYSTEM_PROMPT = """You are an expert Digital Agency specializing in tech and marketing services looking for CLIENTS on Facebook.

YOUR SCOPE:
- Web Development (Frontend, Backend, Full Stack, React, Python, REST API)
- Software (Custom software development, SaaS, MVP building, Software engineer)
- E-commerce (Shopify store setup, Shopify dropshipping, store design)
- AI & Automation (AI bots, n8n workflows, web automation, scraping, ML)
- Design & Marketing (UI/UX design, SEO, Digital Marketing, wordpress website, brand)

CRITICAL RULES:
1. SELLERS: If the author is OFFERING their own services (e.g., "I am a web developer looking for work", "Hire me"), reply exactly: SKIP.
2. SPAM: If the post is a group admin asking people to "join", reply exactly: SKIP.
3. CLIENTS: If the author is a CLIENT asking to HIRE someone, YOU MUST write a comment.
   - This includes: "Need a website", "Looking for a Shopify developer", "We are hiring", "Hiring a Frontend Engineer", "Need someone to build an app".

IF THEY ARE A CLIENT:
- Write a VERY SHORT, confident comment (MAX 2 LINES / 20 words).
- State clearly that you specialize in their exact need.
- End with a strong Call to Action ("Send me a DM", "Let's connect").

Examples:
- Post: "Hi everyone I am a website developer, DM me." -> SKIP (Seller)
- Post: "We’re hiring a Mid-Level Frontend Engineer to help build an AI CRM." -> I specialize in Frontend and React development and can help build your CRM. Let's connect via DM!
- Post: "I need a shopify store built urgently." -> I specialize in building high-converting Shopify stores. Let's connect via DM so we can get this launched for you immediately.
- Post: "Looking for someone to set up n8n automations." -> I am an expert in n8n and web automation. Send me a DM and let's discuss your workflow requirements.
"""

class GenerateCommentView(APIView):
    @extend_schema(
        request=PostTextRequestSerializer,
        responses={
            200: GenerateCommentResponseSerializer,
            400: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        post_text = request.data.get('post_text', '')
        if not post_text:
            return Response({'error': 'post_text required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            response = client.chat.completions.create(
                model="@cf/meta/llama-3.1-8b-instruct-fast", 
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Post: {post_text}"}
                ],
                max_tokens=60,
                temperature=0.3
            )
            comment = response.choices[0].message.content.strip()

            if comment == 'SKIP' or "SKIP" in comment[:10]:
                return Response({'action': 'skip', 'comment': None})

            db_record = GeneratedComment.objects.create(
                post_text=post_text,
                ai_comment=comment,
                status='PENDING'
            )

            return Response({'action': 'comment', 'comment': comment, 'db_id': db_record.id})
            
        except Exception as e:
            print(f"Error: {e}")
            return Response({'action': 'skip', 'error': str(e)}, status=status.HTTP_200_OK)


class UpdateCommentStatusView(APIView):
    @extend_schema(
        request=UpdateCommentStatusRequestSerializer,
        responses={
            200: UpdateCommentStatusResponseSerializer,
            400: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        db_id = request.data.get('db_id')
        new_status = request.data.get('status')
        try:
            record = GeneratedComment.objects.get(id=db_id)
            record.status = new_status
            record.save()
            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CheckPostView(APIView):
    @extend_schema(
        request=PostTextRequestSerializer,
        responses=CheckPostResponseSerializer,
    )
    def post(self, request):
        post_text = request.data.get('post_text', '')
        if not post_text:
            return Response({'exists': False})

        normalized = normalize_post_text(post_text)
        if len(normalized) < 12:
            return Response({'exists': False})

        existing = GeneratedComment.objects.filter(status__in=['POSTED', 'PENDING']).order_by('-created_at')
        for record in existing:
            if not record.post_text:
                continue
            if is_similar_post(record.post_text, post_text):
                return Response({'exists': True})

        return Response({'exists': False})


class IncomingMessageView(APIView):
    @extend_schema(
        request=IncomingMessageRequestSerializer,
        responses={
            200: IncomingMessageResponseSerializer,
            400: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        sender = request.data.get('sender_name', 'Unknown')
        message = request.data.get('message', '')
        
        if not message:
            return Response({'error': 'Message required'}, status=status.HTTP_400_BAD_REQUEST)

        AI_PROMPT = """You are an expert Digital Agency. A client just replied to your comment or messaged you directly.
Read their message and write a short, professional reply. 
Tell them you offer Web Development, Shopify, AI, SEO, and Software services. 
Ask them for more details about their project or tell them to send their requirements via DM/Email.
Keep it under 3 sentences. Be polite and confident."""

        try:
            response = client.chat.completions.create(
                model="@cf/meta/llama-3.1-8b-instruct-fast", 
                messages=[
                    {"role": "system", "content": AI_PROMPT},
                    {"role": "user", "content": f"Client message: {message}"}
                ],
                max_tokens=100,
                temperature=0.6
            )
            ai_reply = response.choices[0].message.content.strip()

            reply_record = IncomingReply.objects.create(
                sender_name=sender,
                client_reply=message,
                ai_response=ai_reply,
                status='REPLIED'
            )

            return Response({'success': True, 'reply': ai_reply, 'id': reply_record.id})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessNotificationView(APIView):
    @extend_schema(
        request=ProcessNotificationRequestSerializer,
        responses=ProcessNotificationResponseSerializer,
    )
    def post(self, request):
        notif_type = request.data.get('type', 'message') 
        sender = request.data.get('sender_name', 'Unknown')
        message = request.data.get('message', '') 

        if notif_type == 'follow':
            ai_reply = f"""Hi {sender}! Thank you for following our page. We specialize in Web Development, Shopify Stores, AI Automation, and Digital Marketing. To celebrate our new connection, we are offering a special discount for new followers! If you need any of these services, just reply to this message and let us know."""
            try:
                IncomingReply.objects.create(
                    sender_name=sender,
                    client_reply=message,
                    ai_response=ai_reply,
                    status='REPLIED'
                )
            except Exception:
                pass
            return Response({'success': True, 'reply': ai_reply})

        if should_skip_business_message(message):
            return Response({'success': True, 'reply': 'SKIP'})

        AI_PROMPT = """You are an expert Digital Agency Salesperson.
Read the client's chat history. They are asking about your services.

Rules:
1. If they ask if you build websites, do SEO, or build Shopify stores, reply "Yes, we do!" and tell them you specialize in exactly that.
2. If they say they have no money or a low budget, offer a smaller payment plan or installments.
3. If they are just saying "Hi" or nothing related to business, reply with exactly: SKIP.

Keep the reply under 3 sentences. Be persuasive. End with a Call to Action asking for their requirements."""

        try:
            response = client.chat.completions.create(
                model="@cf/meta/llama-3.1-8b-instruct-fast", 
                messages=[
                    {"role": "system", "content": AI_PROMPT},
                    {"role": "user", "content": f"Chat History:\n{message}"}
                ],
                max_tokens=120, temperature=0.6
            )
            ai_reply = response.choices[0].message.content.strip()
        except:
            ai_reply = "Yes, we build custom websites and can definitely help you! Could you share a bit more about what your website needs to do?"

        try:
            IncomingReply.objects.create(
                sender_name=sender,
                client_reply=message,
                ai_response=ai_reply,
                status='REPLIED'
            )
        except Exception as e:
            print("DB Error:", e)

        return Response({'success': True, 'reply': ai_reply})
    
class CheckGroupView(APIView):
    @extend_schema(
        request=GroupURLRequestSerializer,
        responses=CheckGroupResponseSerializer,
    )
    def post(self, request):
        url = request.data.get('group_url', '')
        if not url:
            return Response({'exists': False})
        
        exists = JoinedGroup.objects.filter(group_url=url).exists()
        return Response({'exists': exists})

class SaveGroupView(APIView):
    @extend_schema(
        request=GroupURLRequestSerializer,
        responses={
            200: SaveGroupResponseSerializer,
            400: ErrorResponseSerializer,
        },
    )
    def post(self, request):
        url = request.data.get('group_url', '')
        print(f"📥 RECEIVED GROUP URL TO SAVE: {url}")
        
        if url:
            try:
                obj, created = JoinedGroup.objects.get_or_create(group_url=url)
                if created:
                    print(f"✅ SUCCESSFULLY SAVED TO DB: {url}")
                else:
                    print(f"⚠️ ALREADY IN DB: {url}")
                return Response({'success': True, 'created': created})
            except Exception as e:
                print(f"❌ DATABASE ERROR: {e}")
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        return Response({'success': False, 'error': 'No URL provided'}, status=status.HTTP_400_BAD_REQUEST)

class GetWelcomeMessageView(APIView):
    @extend_schema(responses=WelcomeMessageResponseSerializer)
    def get(self, request):
        template = WelcomeTemplate.objects.first()
        
        if not template:
            AI_PROMPT = """Write a friendly 4-line welcome message for a new follower.
Mention that we offer Web Development, Shopify, AI, SEO, and Software services. 
End with a special offer: If they are interested, they get a special discount for being a new follower. 
Keep it professional and exciting."""
            
            try:
                response = client.chat.completions.create(
                    model="@cf/meta/llama-3.1-8b-instruct-fast", 
                    messages=[{"role": "system", "content": AI_PROMPT}],
                    max_tokens=150, temperature=0.7
                )
                welcome_text = response.choices[0].message.content.strip()
            except:
                welcome_text = "Hi there! Thank you for following our page. We specialize in Web Development, Shopify, AI, SEO, and Software services. As a new follower, if you need any of these services, we are offering a special discount just for you! Let's connect and discuss your project."
            
            template = WelcomeTemplate.objects.create(message_text=welcome_text)
            
        return Response({'welcome_text': template.message_text})