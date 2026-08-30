from unittest.mock import patch
from app.chains.normalizer import normalize_query
from app.chains.generator import generate_search_queries
from app.chains.critic import critique_results
from app.chains.synthesizer import synthesize_answer
from app.chains.matcher import MatchedProduct
from app.models.product import ExtractedField, ProductEntity
from app.models.query import Budget, NormalizedQuery


def test_normalizer_fallback_to_heuristic_on_timeout():
    with patch('app.chains.normalizer.build_normalizer_chain', side_effect=TimeoutError('LLM timed out')):
        res = normalize_query('gaming mouse under 2000 with low latency')
        assert res.category in ['gaming mouse', 'mouse']
        assert res.budget.max == 2000
        assert 'purchase' in res.intent


def test_generator_fallback_to_deterministic_queries():
    query = NormalizedQuery(
        intent='purchase',
        category='headphones',
        budget=Budget(min=0, max=5000, currency='INR'),
        constraints=['anc'],
        preferences=[],
        use_case='commute',
        confidence_score=0.9,
    )
    with patch('app.chains.generator.build_generator_chain', side_effect=TimeoutError('LLM timed out')):
        queries = generate_search_queries(query)
        assert len(queries) > 0
        assert any('headphones' in q for q in queries)


def test_critic_fallback_to_deterministic_verdict():
    query = NormalizedQuery(
        intent='purchase',
        category='laptop',
        budget=Budget(min=0, max=60000, currency='INR'),
        constraints=[],
        preferences=[],
        use_case='coding',
        confidence_score=0.9,
    )
    prod = ProductEntity(
        entity_id='test-laptop',
        extracted_at='2026-08-27T00:00:00Z',
        ttl_expires_at='2026-08-28T00:00:00Z',
        fields={
            'price': ExtractedField(value=55000, source_url='https://amazon.in/dp/B0123', snippet=''),
        },
    )
    matched = [MatchedProduct(product=prod, soft_score=8.5, matched_constraints=[])]
    with patch('app.chains.critic.build_critic_chain', side_effect=TimeoutError('LLM timed out')):
        verdict = critique_results(matched, query)
        assert verdict.relevance >= 7
        assert verdict.contradiction_flag is False


def test_synthesizer_fallback_to_template():
    query = NormalizedQuery(
        intent='purchase',
        category='laptop',
        budget=Budget(min=0, max=60000, currency='INR'),
        constraints=[],
        preferences=[],
        use_case='coding',
        confidence_score=0.9,
    )
    prod = ProductEntity(
        entity_id='test-laptop',
        extracted_at='2026-08-27T00:00:00Z',
        ttl_expires_at='2026-08-28T00:00:00Z',
        fields={
            'name': ExtractedField(value='Asus Vivobook', source_url='https://amazon.in/dp/B0123', snippet=''),
            'price': ExtractedField(value=55000, source_url='https://amazon.in/dp/B0123', snippet=''),
        },
    )
    matched = [MatchedProduct(product=prod, soft_score=8.5, matched_constraints=[])]
    with (
        patch('app.chains.synthesizer.build_synthesizer_chain', side_effect=TimeoutError('LLM timed out')),
        patch('app.chains.synthesizer.build_fallback_synthesizer_chain', side_effect=TimeoutError('Fallback timed out')),
    ):
        text = synthesize_answer(matched, query)
        assert 'Asus Vivobook' in text

