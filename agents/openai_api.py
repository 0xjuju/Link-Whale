from decouple import config
import openai
from agents.models import LLM, RAGContext
from companies.models import Company


class LLMFactory:
    """
    Factory class to create instances of a chat-based language model using the OpenAI API.
    The factory uses the latest GPT-4 model (chatGPT 4o) by default.
    """

    def __init__(self, company_name: str, model: str = "gpt-4o") -> None:
        """
        Initialize the LLMFactory by loading the OpenAI API key from the .env file.

        Args:
            company_name (str): Name of Company that will be associated with LLM
            model (str): OpenAI GPT model to use
        """
        # Load the OpenAI API key from the .env file using decouple.config().
        self.api_key: str = config('OPENAI_API_KEY')
        openai.api_key = self.api_key
        self.company_name = company_name
        self.model = model

    def generate_response(self, prompt: str, use_context: bool = True) -> str:
        """
        Generate a response using the chat-based language model for a given prompt.

        Args:
            prompt (str): The prompt to be passed to the model.
            use_context (bool): Whether to use the RAG context associated with the company. Defaults to True.

        Returns:
            str: The response from the model.
        """
        messages = [
            {"role": "user", "content": prompt}
        ]

        if use_context:
            # Load the RAG context from the model using the Company FK
            rag_context = self._get_rag_context()
            context_documents = []
            context_content = "\n".join(context_documents)
            messages.insert(0,
                            {"role": "system", "content": f"Here is some context about the company: {context_content}"})

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages
        )

        return response['choices'][0]['message']['content'].strip()

    @staticmethod
    def create_text_embeddings(documents: list) -> list:
        """
        Create text embeddings for the provided documents using OpenAI's updated embeddings utility.

        Args:
            documents (list): A list of documents to be embedded.

        Returns:
            list: A list of embeddings for the documents.
        """
        embeddings = []
        for doc in documents:
            response = openai.embeddings.create(input=doc, model="text-embedding-ada-002")
            embeddings.append(response.data[0].embedding)
        return embeddings

    def save_rag_context_to_model(self, context_name: str, context_documents: list) -> None:
        """
        Save the RAG context to the Django model (RAGContext).

        Args:
            context_name (str): The name of the RAG context.
            context_documents (list): A list of documents to be used as context.
        """
        embeddings = self.create_text_embeddings(context_documents)
        rag_context = RAGContext.objects.create(
            name=context_name,
            documents=context_documents,
            embeddings=embeddings,
            llm=self._get_llm()
        )
        rag_context.save()

    def _get_llm(self) -> LLM:
        """
        Retrieve or create an LLM model instance associated with a company.

        Returns:
            LLM: The LLM instance associated with the specified company.
        """
        company, _ = Company.objects.get_or_create(name=self.company_name)
        llm, created = LLM.objects.get_or_create(company=company)

        if created:
            llm.model = self.model
            llm.save()

        return llm

    def _get_rag_context(self) -> RAGContext:
        """
        Retrieve or create a RAGContext instance associated with the company.

        Returns:
            RAGContext: The RAGContext instance associated with the specified company.
        """
        llm = self._get_llm()
        rag_context, _ = RAGContext.objects.get_or_create(llm=llm)
        return rag_context

    @staticmethod
    def create_thread(messages: list = None) -> dict:
        """
        Create and return a thread using the OpenAI Assistant API.

        Args:
            messages (list, optional): A list of messages to initialize the thread with. Defaults to None.

        Returns:
            dict: The created thread details.
        """
        response = openai.beta.threads.create(
            messages=messages or [
                {
                    "role": "user",
                    "content": "This is a new thread to start managing summaries."
                }
            ],
        )
        return response

    def create_assistant(self, name: str, description: str = None, tools: list = None,
                         tool_resources: dict = None) -> dict:
        """
        Create and return an assistant for the given thread using the OpenAI Assistant API.

        Args:
            thread_id (str): The ID of the thread to which the assistant belongs.
            name (str): The name of the assistant.
            description (str, optional): A brief description of the assistant. Defaults to None.
            model (str): The model to use for the assistant. Defaults to 'gpt-4o'.
            tools (list, optional): A list of tools for the assistant. Defaults to a code interpreter tool.
            tool_resources (dict, optional): Resources for the tools. Defaults to None.

        Returns:
            dict: The created assistant details.
        """
        response = openai.beta.assistants.create(
            name=name,
            description=description or "An assistant focused on summarizing and verifying document information",
            model=self.model,
            tools=tools or [{"type": "code_interpreter"}],
            tool_resources=tool_resources or {}
        )
        return response

    @staticmethod
    def run(thread_id: str, assistant_id: str) -> dict:
        """
        Run a request with the given assistant within the specified thread and return the response.

        Args:
            thread_id (str): The ID of the thread to which the assistant belongs.
            assistant_id (str): The ID of the assistant to use.

        Returns:
            dict: The response from the assistant.
        """
        response = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
        )
        return response
