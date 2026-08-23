from models.predictor import predict
def test_predict_returns_expected_keys():
    result = predict("Government publishes an official research report.")
    assert "prediction" in result
    assert "confidence" in result
