import os
import requests
import json
import logging
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import asyncio
import io

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration - Environment Variables se le
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8089748380:AAEiufxHnXzSVZUFxGS6z-f0YSzbDL63ZtM")
API_URL = "https://api.yabes-desu.workers.dev/ai/tool/txt2video"
WELCOME_IMAGE_URL = "https://uploads.onecompiler.io/43sb938uw/43xc7jtk7/e54960e4-6f62-4dc2-9286-0385c4d7b9db.jpeg"

# Channel Configuration
CHANNELS = [
    {"id": "@Owner_By_Rose", "name": "Main Channel", "url": "https://t.me/Owner_By_Rose"},
    {"id": "@Rose_X_Files", "name": "Second Channel", "url": "https://t.me/Rose_X_Files"}
]

DEVELOPER_ID = "@Ros3_Zii"

# Store user verification status
user_verification = {}

async def check_user_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is subscribed to all required channels"""
    try:
        for channel in CHANNELS:
            try:
                chat_member = await context.bot.get_chat_member(chat_id=channel["id"], user_id=user_id)
                if chat_member.status in ['left', 'kicked']:
                    logger.info(f"User {user_id} not subscribed to {channel['id']}")
                    return False
            except Exception as e:
                logger.error(f"Error checking channel {channel['id']}: {e}")
                return False
        return True
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id}: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    user_id = update.effective_user.id
    logger.info(f"Start command received from user {user_id}")
    
    # Check if user is verified
    if user_id in user_verification and user_verification[user_id]:
        await send_welcome_message(update)
        return
    
    # Check subscription status
    is_subscribed = await check_user_subscription(user_id, context)
    
    if is_subscribed:
        user_verification[user_id] = True
        await send_welcome_message(update)
    else:
        await send_subscription_message(update)

async def send_subscription_message(update: Update):
    """Send channel subscription message"""
    try:
        keyboard = []
        
        for channel in CHANNELS:
            keyboard.append([InlineKeyboardButton(f"📢 Join {channel['name']}", url=channel["url"])])
        
        keyboard.append([InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_ID[1:]}")])
        keyboard.append([InlineKeyboardButton("✅ I've Joined All Channels", callback_data="check_subscription")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        subscription_text = """
🔒 **Channel Membership Required** 🔒

To use this AI Video Generator bot, you need to join our channels first!

**Required Channels to Join:**
📢 Main Channel - @Owner_By_Rose
📢 Second Channel - @Rose_X_Files  
👨‍💻 Developer - @Ros3_Zii

**Steps:**
1. Join all channels above
2. Click the 'I've Joined All Channels' button
3. Start generating amazing videos! 🎬

Note: Make sure you've joined ALL channels before verifying!
        """
        
        # Try to send with photo first
        try:
            response = requests.get(WELCOME_IMAGE_URL, timeout=10)
            if response.status_code == 200:
                photo = InputFile(io.BytesIO(response.content), filename="welcome.jpg")
                await update.message.reply_photo(
                    photo=photo,
                    caption=subscription_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
        except Exception as e:
            logger.warning(f"Could not send photo: {e}")
        
        # Fallback to text message
        await update.message.reply_text(
            subscription_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in subscription message: {e}")
        await update.message.reply_text(
            "Please join our channels to use this bot!",
            reply_markup=reply_markup
        )

async def send_welcome_message(update: Update):
    """Send welcome message after verification"""
    try:
        welcome_text = """
🎬 **Welcome to AI Video Generator Bot!** 🎬

✅ **Verification Successful!**

Now you can create amazing videos from text prompts using advanced AI technology.

**How to use:**
Simply send me any text description of the video you want to create!

**Example prompts:**
• "A beautiful sunset over mountains with flying eagles"
• "A cat dancing in the rain with colorful umbrella"
• "Futuristic city with flying cars and neon lights"

**Features:**
✓ No prompt length restrictions
✓ High quality video generation
✓ Fast processing
✓ Unlimited generations

Send me your creative prompt now! ✨
        """
        
        # Try to send with photo first
        try:
            response = requests.get(WELCOME_IMAGE_URL, timeout=10)
            if response.status_code == 200:
                photo = InputFile(io.BytesIO(response.content), filename="welcome.jpg")
                await update.message.reply_photo(
                    photo=photo,
                    caption=welcome_text,
                    parse_mode='Markdown'
                )
                return
        except Exception as e:
            logger.warning(f"Could not send welcome photo: {e}")
        
        # Fallback to text message
        await update.message.reply_text(
            welcome_text,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error in welcome message: {e}")
        await update.message.reply_text(
            "🎬 Welcome to AI Video Generator Bot! ✅ Verified! Send me any text prompt to generate videos! ✨"
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    user_id = query.from_user.id
    
    await query.answer()
    
    if query.data == "check_subscription":
        # Check subscription status
        is_subscribed = await check_user_subscription(user_id, context)
        
        if is_subscribed:
            user_verification[user_id] = True
            # Edit the original message
            await query.edit_message_caption(
                caption="✅ **Verification Successful!**\n\nYou can now use the bot. Send me a text prompt to generate amazing videos! 🎬",
                parse_mode='Markdown'
            )
            # Send welcome message separately
            await send_welcome_after_verification(context, query.message.chat_id)
        else:
            await query.answer("❌ Please join ALL channels first! Then click this button again.", show_alert=True)

async def send_welcome_after_verification(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Send welcome message after verification from callback"""
    try:
        welcome_text = """
🎬 **Ready to Generate Videos!** 🎬

Now you can create amazing AI videos from any text prompt!

**Just send me any description like:**
"A beautiful sunset over mountains"
"A cat dancing in rain"
"Futuristic city with flying cars"

No restrictions on prompt length! Send your first prompt now! ✨
        """
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error sending welcome after verification: {e}")

def generate_video(prompt: str):
    """Generate video using the API"""
    try:
        # Prepare the API request with proper parameters
        params = {'prompt': prompt}
        
        logger.info(f"Generating video for prompt (length: {len(prompt)}): {prompt[:100]}...")
        
        # Make API request with longer timeout
        timeout = 120  # 2 minutes timeout
        response = requests.get(API_URL, params=params, timeout=timeout)
        
        logger.info(f"API Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"API Response: {result}")
            
            if result.get('success'):
                video_url = result.get('url')
                if video_url:
                    logger.info(f"Video generated successfully: {video_url}")
                    return video_url
                else:
                    logger.error("No URL in response")
                    return None
            else:
                logger.error(f"API returned success false: {result}")
                return None
        else:
            logger.error(f"API request failed with status: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in generate_video: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages and generate videos"""
    user_id = update.effective_user.id
    prompt = update.message.text.strip()
    
    logger.info(f"Message received from user {user_id}: {prompt[:50]}...")
    
    # Check if user is verified
    if user_id not in user_verification or not user_verification[user_id]:
        is_subscribed = await check_user_subscription(user_id, context)
        if not is_subscribed:
            await update.message.reply_text("❌ Please verify your channel membership first using /start")
            await send_subscription_message(update)
            return
        else:
            user_verification[user_id] = True
    
    if not prompt:
        await update.message.reply_text("Please send a text prompt to generate a video.")
        return
    
    # No prompt length restrictions
    if len(prompt) < 2:
        await update.message.reply_text("Please provide a more detailed prompt.")
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🔄 **Processing your request...**\n\n"
        f"📝 Prompt: {prompt[:300]}{'...' if len(prompt) > 300 else ''}\n\n"
        f"⏳ Generating video... Please wait (this may take 1-2 minutes)",
        parse_mode='Markdown'
    )
    
    try:
        # Generate video
        logger.info(f"Starting video generation for user {user_id}")
        video_url = await asyncio.to_thread(generate_video, prompt)
        
        if video_url:
            logger.info(f"Video generated, downloading from: {video_url}")
            
            # Download the video with timeout
            try:
                video_response = requests.get(video_url, timeout=60)
                
                if video_response.status_code == 200:
                    # Send video as file
                    video_file = InputFile(
                        io.BytesIO(video_response.content),
                        filename="ai_video.mp4"
                    )
                    
                    caption = f"🎬 **Your AI Generated Video**\n\n📝 Prompt: {prompt}\n\nEnjoy! 😊"
                    
                    # Delete processing message first
                    await processing_msg.delete()
                    
                    # Send the video
                    await update.message.reply_video(
                        video=video_file,
                        caption=caption,
                        parse_mode='Markdown'
                    )
                    
                    logger.info(f"Video sent successfully to user {user_id}")
                    
                else:
                    await processing_msg.edit_text(
                        "❌ Error downloading the generated video. Please try again."
                    )
                    logger.error(f"Video download failed with status: {video_response.status_code}")
                    
            except Exception as download_error:
                await processing_msg.edit_text(
                    "❌ Error downloading video. The API might be busy. Please try again in a moment."
                )
                logger.error(f"Download error: {download_error}")
                
        else:
            await processing_msg.edit_text(
                "❌ Sorry, I couldn't generate a video for your prompt. "
                "This might be due to:\n"
                "• API temporary issue\n"
                "• Server overload\n"
                "• Complex prompt\n\n"
                "Please try again in a moment with the same or slightly modified prompt."
            )
            logger.error(f"Video generation failed for user {user_id}")
            
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        try:
            await processing_msg.edit_text(
                "❌ An unexpected error occurred. Please try again with your prompt."
            )
        except:
            await update.message.reply_text(
                "❌ An error occurred. Please try again."
            )

async def force_verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force re-verification command"""
    user_id = update.effective_user.id
    if user_id in user_verification:
        del user_verification[user_id]
    
    await update.message.reply_text("🔍 Checking your channel membership...")
    await send_subscription_message(update)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please use /start to try again."
            )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

def main():
    """Start the bot"""
    try:
        # Create the Application
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("verify", force_verify))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Start the Bot
        print("🤖 Bot is starting...")
        print("✅ Channel verification enabled")
        print("✅ Video generation ready")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Bot failed to start: {e}")

if __name__ == '__main__':
    main()
