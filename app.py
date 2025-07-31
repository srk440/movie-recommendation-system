import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load datasets from local path
def load_data():
    movies = pd.read_csv("DATA_set/ml-32m/movies.csv")
    tags = pd.read_csv("DATA_set/ml-32m/tags.csv")

    # Load only top 5000 movies to reduce memory usage
    top_movies = movies.head(5000)
    tags = tags[tags['movieId'].isin(top_movies['movieId'])]
    return top_movies, tags


# Preprocess and compute similarity
def preprocess_and_compute(movies, tags):
    # Ensure tags are strings (handle NaNs safely)
    tags['tag'] = tags['tag'].astype(str).fillna('')

    # Group tags per movie
    tags_grouped = tags.groupby('movieId')['tag'].apply(lambda x: ' '.join([str(i) for i in x])).reset_index()
    tags_grouped.rename(columns={'tag': 'keywords'}, inplace=True)

    # Merge with movies
    movies = pd.merge(movies, tags_grouped, on='movieId', how='left')
    movies['keywords'] = movies['keywords'].fillna('')
    movies['genres'] = movies['genres'].fillna('')

    # Combine features
    movies['combined_features'] = movies['genres'] + " " + movies['keywords']
    movies['combined_features'] = movies['combined_features'].fillna('')

    # TF-IDF
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(movies['combined_features'])

    # Cosine Similarity
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    return movies, cosine_sim

# Convert similarity score to stars
def similarity_to_stars(score):
    if score >= 0.8:
        return "⭐⭐⭐⭐⭐"
    elif score >= 0.6:
        return "⭐⭐⭐⭐"
    elif score >= 0.4:
        return "⭐⭐⭐"
    elif score >= 0.2:
        return "⭐⭐"
    else:
        return "⭐"

# Recommend similar movies
def recommend_movies(movie_title, movies_df, similarity_matrix):
    if movie_title not in movies_df['title'].values:
        return f"'{movie_title}' not found in the dataset."
    
    idx = movies_df[movies_df['title'] == movie_title].index[0]
    similarity_scores = list(enumerate(similarity_matrix[idx]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    top_movies = similarity_scores[1:11]

    recommendations = []
    for i in top_movies:
        movie_idx = i[0]
        stars = similarity_to_stars(i[1])
        recommendations.append((movies_df['title'].iloc[movie_idx], stars))
    return recommendations

# Streamlit UI
def main():
    st.set_page_config(
        page_title="Movie Recommendation System",
        page_icon="🎥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    background_image = """
    <style>
    .stApp {
        background-image: url('https://cdn.pixabay.com/photo/2017/07/02/18/46/film-2467396_1280.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: white;
    }
    </style>
    """
    st.markdown(background_image, unsafe_allow_html=True)

    st.title("🎬 Movie Recommendation System")
    st.subheader("Find movies similar to your favorite one!")

    with st.spinner("Loading data and computing similarity..."):
        movies, tags = load_data()
        movies, cosine_sim = preprocess_and_compute(movies, tags)

    selected_movie = st.text_input("Enter a movie title (e.g., 'Toy Story (1995)')", "")

    if st.button("Get Recommendations"):
        if selected_movie:
            recommendations = recommend_movies(selected_movie, movies, cosine_sim)
            if isinstance(recommendations, str):
                st.error(recommendations)
            else:
                st.subheader(f"Movies similar to '{selected_movie}':")
                for movie, stars in recommendations:
                    st.markdown(f"- **{movie}**: {stars}")
        else:
            st.warning("Please enter a movie title.")

if __name__ == "__main__":
    main()
