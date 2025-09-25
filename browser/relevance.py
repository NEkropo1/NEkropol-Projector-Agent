from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def score_relevance(query: str, texts: List[str]) -> List[float]:
    vect = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
    x = vect.fit_transform([query] + texts)
    sims = cosine_similarity(x[0], x[1:]).ravel().tolist()
    return sims
