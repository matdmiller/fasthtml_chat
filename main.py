from fasthtml.common import *
from monsterui.all import * 
import os
import json
from openai import OpenAI

# Create FastHTML app with HTMX websocket extension
app, rt = fast_app(exts='ws', hdrs=Theme.zinc.headers())

DEFAULT_HISTORY = [
    {"role": "system", "content": "You are a helpful assistant that can answer questions and help with tasks."},
    {"role": "assistant", "content": "Hello! I'm the AI Chat Assistant. How can I help you today?"},
    {"role": "user", "content": "What is the capital of the moon?"},
    {"role": "assistant", "content": "The capital of the moon is called 'The Moon' and is located on the moon."},
    {"role": "user", "content": "What is the capital of the moon?"},
    {"role": "assistant", "content": "The capital of the moon is called 'The Moon' and is located on the moon."},
    {"role": "user", "content": "What is the capital of the moon?"},
    {"role": "assistant", "content": "The capital of the moon is called 'The Moon' and is located on the moon."},
]

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def ChatMessage(role, content):
    """Creates a styled chat message bubble"""
    colors = {
        'system': {'bg': 'bg-gray-200', 'text': 'text-gray-800'},
        'user': {'bg': 'bg-blue-500', 'text': 'text-white'},
        'assistant': {'bg': 'bg-gray-200', 'text': 'text-gray-800'}
    }
    style = colors.get(role.lower(), colors['system'])
    
    align_cls = 'justify-end' if role.lower() == 'user' else 'justify-start'
    
    return Div(cls=f'flex {align_cls} mb-4')(
        Div(cls=f'{style["bg"]} {style["text"]} rounded-2xl p-4 max-w-[80%]')(
            Strong(role.capitalize(), cls='text-sm font-semibold tracking-wide'),
            Div(content, cls='mt-2')
        )
    )

def create_chat_messages_ui(messages: list[dict]=[]):
    return Div(
        *[ChatMessage(msg["role"], msg["content"]) for msg in messages],
        Script("document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight;"),
        id="chat-messages",
        hx_swap_oob="true",
        cls=("pt-16", "pb-24")
    )

def create_chat_input(history: list[dict]=tuple()):
    return Div(
        Form(
            DivFullySpaced(
                TextArea(
                    id="message", 
                    placeholder="Type your message...", 
                    autofocus=True,
                    hx_on_keydown="""if((event.ctrlKey || event.metaKey || event.shiftKey) && event.key === 'Enter') 
                    { event.preventDefault(); this.closest('form').requestSubmit(); }"""
                ),
                Button(
                    "Send", 
                    id="send-button",
                    type="submit", 
                    cls=("ml-2", ButtonT.primary),
                    uk_tooltip="Press Ctrl+Enter, Cmd+Enter, or Shift+Enter to send"
                ),
                cls="flex items-end gap-2"
            ),
            Input(type="hidden", id="history", value=json.dumps(history)),
            hx_post="/send",
            hx_target="#chat-input",
            hx_swap="outerHTML",
            id="chat-input",
            onsubmit="(() => {b = document.getElementById('send-button'); b.disabled = true; b.innerHTML = '<div uk-spinner></div>';})();"
        ), 
        cls="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 shadow-lg"
    )

def create_navbar():
    return NavBar(
        A("Home", href="#"),
        A("Chat History", href="#"),
        A("Settings", href="#"),
        brand=H3("AI Chat Assistant"),
        sticky=True,
        cls="px-6 py-3 shadow-sm bg-background z-50 fixed top-0 left-0 right-0 w-full"
    )

@rt('/')
def homepage():
    return Container(
        create_navbar(),
        Div(create_chat_messages_ui(DEFAULT_HISTORY), id="chat-container"),
        create_chat_input()
    )

@rt('/send', methods=['POST'])
def send_message(message: str, history: str):
    if not message.strip():
        return create_chat_input(json.loads(history))
    
    chat_history = json.loads(history)
    chat_history.append({"role": "user", "content": message})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=chat_history
        )
        
        assistant_message = response.choices[0].message.content
        
        # Add assistant response to history
        chat_history.append({"role": "assistant", "content": assistant_message})
        return create_chat_input(chat_history), create_chat_messages_ui(chat_history)
    
    except Exception as e:
        return Alert(f"Error: {str(e)}", cls=AlertT.error)

# Run the app
serve()