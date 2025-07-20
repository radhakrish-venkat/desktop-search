import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def test_client():
    return TestClient(app)

def test_llm_status(test_client):
    response = test_client.get("/api/v1/llm/status")
    assert response.status_code == 200
    data = response.json()
    assert "active_provider" in data
    assert "available_providers" in data
    assert "embedding_model" in data
    assert "llm_model" in data


def test_llm_available_models(test_client):
    response = test_client.get("/api/v1/llm/models/available")
    assert response.status_code == 200
    data = response.json()
    assert "llm_models" in data
    assert "embedding_models" in data
    assert any(m["name"] == "phi3" for m in data["llm_models"])
    assert any(m["name"] == "bge-small-en" for m in data["embedding_models"])


def test_llm_available_providers(test_client):
    response = test_client.get("/api/v1/llm/providers/available")
    assert response.status_code == 200
    data = response.json()
    assert "detected_providers" in data
    assert "providers" in data


def test_llm_configure_models(test_client):
    payload = {
        "llm_model": "phi3",
        "embedding_model": "bge-small-en",
        "llm_max_tokens": 512,
        "llm_temperature": 0.5,
        "llm_top_p": 0.8
    }
    response = test_client.post("/api/v1/llm/config", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "llm_model" in data["config"]
    assert data["config"]["llm_model"] == "phi3"
    assert data["config"]["embedding_model"] == "bge-small-en"


def test_llm_enhanced_search(test_client):
    payload = {
        "query": "test document",
        "max_results": 3,
        "use_llm": False
    }
    response = test_client.post("/api/v1/llm/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["enhanced"] is False


def test_llm_enhanced_search_with_llm(test_client, monkeypatch):
    # Patch the LLM manager to simulate a response
    from pkg.llm import local_llm
    class DummyProvider:
        def generate_response(self, prompt, context=""):
            return "Dummy LLM response"
        is_loaded = True
        config = type("Config", (), {"llm_model": "phi3"})()

    manager = local_llm.get_llm_manager()
    manager.active_provider = DummyProvider()

    payload = {
        "query": "test document",
        "max_results": 2,
        "use_llm": True
    }
    response = test_client.post("/api/v1/llm/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["enhanced"] is True
    assert "llm_response" in data
    assert data["llm_response"] == "Dummy LLM response"


def test_llm_question_answering(test_client, monkeypatch):
    from pkg.llm import local_llm
    class DummyProvider:
        def generate_response(self, prompt, context=""):
            return "Dummy answer"
        is_loaded = True
        config = type("Config", (), {"llm_model": "phi3"})()
    manager = local_llm.get_llm_manager()
    manager.active_provider = DummyProvider()
    payload = {
        "question": "What is this?",
        "query": "test document",
        "max_results": 2
    }
    response = test_client.post("/api/v1/llm/question", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["answered"] is True
    assert data["answer"] == "Dummy answer"


def test_llm_summary(test_client, monkeypatch):
    from pkg.llm import local_llm
    class DummyProvider:
        def generate_response(self, prompt, context=""):
            return "Dummy summary"
        is_loaded = True
        config = type("Config", (), {"llm_model": "phi3"})()
    manager = local_llm.get_llm_manager()
    manager.active_provider = DummyProvider()
    payload = {
        "query": "test document",
        "max_results": 2
    }
    response = test_client.post("/api/v1/llm/summary", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["summarized"] is True
    assert data["summary"] == "Dummy summary" 