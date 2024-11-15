from django.test import TestCase
from unittest.mock import patch, MagicMock
from agents.models import LLM, RAGContext
from companies.models import Company
from agents.openai_api import LLMFactory


class LLMFactoryTest(TestCase):
    def setUp(self):
        # Set up a test company and LLMFactory instance
        self.company_name = "Test Company"
        self.model = "gpt-4o"
        self.factory = LLMFactory(company_name=self.company_name, model=self.model)
        self.company = Company.objects.create(name=self.company_name)

    @patch("openai.ChatCompletion.create")
    def test_generate_response(self, mock_create):
        # Mocking the response from OpenAI API
        mock_create.return_value = {"choices": [{"message": {"content": "Test response"}}]}
        response = self.factory.generate_response(prompt="Test prompt")
        self.assertEqual(response, "Test response")
        mock_create.assert_called_once()

    @patch("openai.embeddings.create")
    def test_create_text_embeddings(self, mock_create):
        # Mocking the response from OpenAI Embedding API
        mock_create.return_value = MagicMock()
        mock_create.return_value.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        documents = ["Document 1", "Document 2"]
        embeddings = self.factory.create_text_embeddings(documents)
        self.assertEqual(len(embeddings), 2)
        self.assertEqual(embeddings[0], [0.1, 0.2, 0.3])
        mock_create.assert_called()

    def test_save_rag_context_to_model(self):
        # Test saving RAG context to model
        context_name = "Test Context"
        context_documents = ["Doc 1", "Doc 2"]
        self.factory.save_rag_context_to_model(context_name, context_documents)
        rag_context = RAGContext.objects.get(name=context_name)
        self.assertEqual(rag_context.name, context_name)
        self.assertEqual(rag_context.documents, context_documents)
        self.assertEqual(rag_context.llm.company.name, self.company_name)

    def test_get_llm(self):
        # Test retrieving or creating an LLM instance
        llm = self.factory._get_llm()
        self.assertIsInstance(llm, LLM)
        self.assertEqual(llm.company.name, self.company_name)
        self.assertEqual(llm.model, self.model)

    @patch("openai.beta.threads.create")
    def test_create_thread(self, mock_create):
        # Mocking the response from OpenAI API for creating a thread
        mock_create.return_value = {"id": "test_thread_id"}
        response = self.factory.create_thread()
        self.assertEqual(response["id"], "test_thread_id")
        mock_create.assert_called_once()

    @patch("openai.beta.assistants.create")
    def test_create_assistant(self, mock_create):
        # Mocking the response from OpenAI API for creating an assistant
        mock_create.return_value = {"id": "test_assistant_id"}
        response = self.factory.create_assistant(name="Test Assistant")
        self.assertEqual(response["id"], "test_assistant_id")
        mock_create.assert_called_once()

    @patch("openai.beta.threads.runs.create")
    def test_run(self, mock_run):
        # Mocking the response from OpenAI API for running a thread
        mock_run.return_value = {"id": "test_run_id", "result": "Run result"}
        response = LLMFactory.run(thread_id="test_thread_id", assistant_id="test_assistant_id", prompt="Test prompt")
        self.assertEqual(response["id"], "test_run_id")
        self.assertEqual(response["result"], "Run result")
        mock_run.assert_called_once()



