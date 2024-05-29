Advanced Context-Aware Telegram Chatbot

A powerful chatbot for message processing and context understanding using LM-Studio and various language models.
Features

    Verification and processing of incoming text messages
    Contextual response generation
    Integration of time, date, and user information
    Utilization of LM-Studio for local language models

Installation

    Python Version: Ensure Python 3.8 or higher is installed.
    Clone the repository::

```bash
git clone https://github.com/dolmario/chatbot_context_understanding.git
cd chatbot_context_understanding
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

Usage

Start the bot with:

```bash
python main.py
```

Message Processing Functions and Model Types

The message processing functions of the chatbot are fundamental for its interaction with users. These encompass a series of steps ensuring that incoming messages are efficiently analyzed and appropriately handled.

    Incoming Message Verification: The first step involves verifying and determining the type of incoming messages (text, document, image, or voice) as soon as they enter the system. This analysis ensures proper handling and response generation based on the message type.

    Text Message Processing: For text messages, the chatbot extracts the raw text and prepares it for further processing steps, including removing formatting, tokenizing the text, and filtering out stopwords. The goal is to transform the text into a suitable format for analysis and processing by the chatbot.

    Integration of Time, Date, and User Information: Besides processing text messages, the chatbot also considers time, date, and user information. Analyzing these details enables the chatbot to generate personalized and context-aware responses. For instance, it can consider the current date and time to answer time-related queries and use user information to facilitate personalized interactions.

    Model Types and Processing with LM-Studio: The chatbot uses various model types, particularly for generating responses. This includes integrating models from LM-Studio, a powerful tool for creating and customizing language models.

        Model Types: The chatbot employs different models for specific tasks, such as the Llama 3 model. This model is optimized for instructions and offers quick and precise performance. Trained on over 15 trillion tokens, it encompasses a wide range of topics and languages, making it suitable for general conversations, knowledge inquiries, and programming tasks.

        Processing with LM-Studio: LM-Studio is a desktop application that allows local LLMs (like the Llama 3 model) to run on your computer. The LM-Studio API provides various functions, including message processing and response generation. Through the API, you can send text inputs to the model and retrieve generated responses.

        Integration in Message Processing: The integration with LM-Studio is seamlessly embedded into the chatbot's message processing. Incoming messages are sent to the local LLM, which then generates appropriate responses. Utilizing LM-Studio enables the chatbot to consider contextual information and user preferences, providing personalized responses.

Message Caching and Purpose of Storage

The caching of messages serves several purposes and is a crucial component of the chatbot's message processing functions.

    History and Context: Storing messages allows the chatbot to track the conversation history with a user and consider the context of previous messages. This helps the chatbot understand relevant information and topics to respond appropriately.

    Message Review: By storing messages, the chatbot can access past messages and extract relevant information to generate context-aware responses. This enables the chatbot to analyze the conversation history and generate appropriate replies based on the previous conversation flow.

    User Experience and Personalization: Storing messages enhances the user experience by enabling the chatbot to provide personalized and context-based interactions. By considering past messages, the chatbot can better understand the user's needs and preferences, delivering relevant responses accordingly.



