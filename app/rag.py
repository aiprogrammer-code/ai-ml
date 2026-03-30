import re
from sentence_transformers import SentenceTransformer
from endee.endee import Endee   # ✅ FIXED IMPORT

model = SentenceTransformer("all-MiniLM-L6-v2")


def get_client():
    return Endee()

#test
def create_index_if_not_exists(client, index_name="resume_jd_index", dimension=384):
    try:
        client.create_index(
            name=index_name,
            dimension=dimension,
            space_type="cosine"
        )
        print(f"Index '{index_name}' created.")
    except Exception as e:
        print(f"Index may already exist: {e}")

    return client.get_index(index_name)


def store_chunks(index, chunks, source_name):
    records = []
    embeddings = model.encode(chunks)

    for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        records.append({
            "id": f"{source_name}_{i}",
            "vector": emb.tolist(),
            "meta": {
                "text": chunk,
                "source": source_name
            },
            "filter": {
                "doc_type": source_name
            }
        })

    index.upsert(records)


def search_chunks(index, query, top_k=5):
    query_vector = model.encode(query).tolist()
    results = index.query(vector=query_vector, top_k=top_k)
    return results


def generate_simple_answer(results, question):
    context = "\n\n".join(
        [r["meta"].get("text", "") for r in results if "meta" in r]
    )

    answer = f"""
Question: {question}

Top Matching Content:
{context[:2000]}
"""
    return answer


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("-", " ")
    text = text.replace("/", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_skill_from_question(question: str):
    q = normalize_text(question)

    patterns = [
        r"is it having (.+)",
        r"does it have (.+)",
        r"does the resume have (.+)",
        r"is (.+) present",
        r"is (.+) available",
        r"has (.+)",
        r"do we have (.+)",
        r"whether (.+) is present",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            skill = match.group(1).strip()
            skill = re.sub(r"\b(skill|experience|knowledge)\b", "", skill).strip()
            return skill

    return None


def get_skill_aliases(skill: str):
    aliases_map = {
        "micro services": ["microservices", "micro services", "micro service", "micro-service"],
        "microservice": ["microservices", "micro services", "micro service", "micro-service"],
        "spring boot": ["spring boot"],
        "java": ["java"],
        "aws": ["aws", "amazon web services"],
        "docker": ["docker"],
        "kubernetes": ["kubernetes", "k8s"],
        "hibernate": ["hibernate"],
        "jpa": ["jpa"],
        "rest api": ["rest api", "rest apis", "restful api", "restful apis"],
        "react": ["react", "reactjs", "react js"],
        "kafka": ["kafka", "apache kafka"],
        "redis": ["redis"],
        "jwt": ["jwt", "json web token"],
        "oauth": ["oauth", "oauth2", "oauth 2"],
        "ci cd": ["ci cd", "cicd", "ci/cd", "continuous integration", "continuous delivery"],
        "messaging systems": ["messaging systems", "messaging", "event streaming"],
        "cloud native development": ["cloud native development", "cloud native"],
        "vector databases": ["vector databases", "vector database"],
        "elasticsearch": ["elasticsearch"],
    }

    normalized_skill = normalize_text(skill)

    if normalized_skill in aliases_map:
        return aliases_map[normalized_skill]

    return [normalized_skill]


def check_skill_in_resume(question: str, resume_text: str):
    skill = extract_skill_from_question(question)
    if not skill:
        return None

    normalized_resume = normalize_text(resume_text)
    aliases = get_skill_aliases(skill)

    for alias in aliases:
        if alias in normalized_resume:
            return {
                "answer": "YES",
                "skill": skill,
                "matched_keyword": alias
            }

    return {
        "answer": "NO",
        "skill": skill,
        "matched_keyword": None
    }


def extract_candidate_skills(text: str):
    text_n = normalize_text(text)

    known_skills = [
        "java",
        "spring boot",
        "microservices",
        "aws",
        "docker",
        "kubernetes",
        "hibernate",
        "jpa",
        "rest api",
        "redis",
        "jwt",
        "oauth",
        "react",
        "kafka",
        "ci cd",
        "messaging systems",
        "cloud native development",
        "vector databases",
        "elasticsearch",
    ]

    found = set()

    for skill in known_skills:
        aliases = get_skill_aliases(skill)
        for alias in aliases:
            if normalize_text(alias) in text_n:
                found.add(skill)
                break

    return sorted(found)


def analyze_resume_vs_jd(resume_text: str, jd_text: str):
    resume_skills = set(extract_candidate_skills(resume_text))
    jd_skills = set(extract_candidate_skills(jd_text))

    matched_skills = sorted(resume_skills.intersection(jd_skills))
    missing_skills = sorted(jd_skills - resume_skills)
    extra_skills = sorted(resume_skills - jd_skills)

    match_percentage = 0
    if jd_skills:
        match_percentage = round((len(matched_skills) / len(jd_skills)) * 100, 2)

    return {
        "resume_skills": sorted(resume_skills),
        "jd_skills": sorted(jd_skills),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills,
        "match_percentage": match_percentage
    }