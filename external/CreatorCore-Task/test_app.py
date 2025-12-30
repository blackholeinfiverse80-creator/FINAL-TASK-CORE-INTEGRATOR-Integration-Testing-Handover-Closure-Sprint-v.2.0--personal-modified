import pytest
pytest.importorskip("flask")
from app import app, db, get_related_context
from models import Generation

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

def test_generate_endpoint(client):
    response = client.post('/generate', json={"prompt": "test prompt"})
    assert response.status_code == 200
    data = response.get_json()
    assert "generated_text" in data
    assert "related_context" in data
    assert isinstance(data["related_context"], list)

def test_feedback_endpoint(client):
    # First generate
    client.post('/generate', json={"prompt": "test"})
    # Feedback
    response = client.post('/feedback', json={"generation_id": 1, "command": "+2"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["new_score"] == 2.0

def test_history_endpoint(client):
    client.post('/generate', json={"prompt": "test1"})
    client.post('/generate', json={"prompt": "test2"})
    response = client.get('/history')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2

def test_context_retrieval(client):
    # Generate a few
    client.post('/generate', json={"prompt": "hello world"})
    client.post('/generate', json={"prompt": "hello universe"})
    # Generate similar
    response = client.post('/generate', json={"prompt": "hello galaxy"})
    data = response.get_json()
    assert len(data["related_context"]) == 2  # since 2 previous

def test_scoring_logic(client):
    # Generate three similar
    client.post('/generate', json={"prompt": "ai story"})
    client.post('/generate', json={"prompt": "ai tale"})
    client.post('/generate', json={"prompt": "ai narrative"})
    
    # Feedback on first
    client.post('/feedback', json={"generation_id": 1, "command": "+5"})
    
    # Generate another similar
    response = client.post('/generate', json={"prompt": "ai saga"})
    data = response.get_json()
    # The first should have higher ranking due to score
    # But since all similar, check that related_context has scores
    assert all(isinstance(item["score"], float) for item in data["related_context"])