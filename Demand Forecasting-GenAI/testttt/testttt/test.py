from groq import Groq

# Replace 'your_api_key_here' with your actual API key
client = Groq(api_key="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")

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Explain the importance of fast language models",
        }
    ],
    model="llama3-8b-8192",
)

print(chat_completion.choices[0].message.content)
