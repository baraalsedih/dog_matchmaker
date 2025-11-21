"""
Generate social media posts for dog breed matches.
"""

def generate_social_post(row, prefs=None):
    """
    Generate a short, engaging social media post for a breed match.
    
    Args:
        row: DataFrame row with breed information
        prefs: Optional preferences dict for personalized messaging
    
    Returns:
        str: Social media-ready post text
    """
    breed_name = row['breed']
    score = row.get('score', 0)
    
    # Get key characteristics
    energy = row.get('energy', 3)
    trainability = row.get('trainability', 3)
    good_with_kids = row.get('good_with_kids', 3)
    shedding = row.get('shedding', 3)
    playfulness = row.get('playfulness', 3)
    affection = row.get('affection', 3)
    
    # Build engaging headline
    headlines = [
        f"🐕 Meet your perfect match: {breed_name}!",
        f"✨ Your ideal companion: {breed_name}",
        f"🎯 Found my dream dog: {breed_name}!",
        f"💕 Perfect match: {breed_name}",
    ]
    import random
    headline = random.choice(headlines)
    
    # Build key highlights
    highlights = []
    
    # Energy level description
    if energy >= 4:
        highlights.append("high-energy")
    elif energy <= 2:
        highlights.append("calm & relaxed")
    else:
        highlights.append("moderate energy")
    
    # Trainability
    if trainability >= 4:
        highlights.append("highly trainable")
    elif trainability <= 2:
        highlights.append("independent")
    else:
        highlights.append("trainable")
    
    # Kid-friendly
    if good_with_kids >= 4:
        highlights.append("great with kids")
    
    # Shedding
    if shedding <= 2:
        highlights.append("low shedding")
    elif shedding >= 4:
        highlights.append("heavy shedder")
    
    # Playfulness
    if playfulness >= 4:
        highlights.append("very playful")
    
    # Affection
    if affection >= 4:
        highlights.append("super affectionate")
    
    # Build the post
    post_parts = [headline]
    post_parts.append("")
    
    # Add match score
    if score >= 0.85:
        post_parts.append(f"Match Score: {score:.1%} ⭐⭐⭐")
    elif score >= 0.75:
        post_parts.append(f"Match Score: {score:.1%} ⭐⭐")
    else:
        post_parts.append(f"Match Score: {score:.1%} ⭐")
    
    post_parts.append("")
    
    # Key traits
    if highlights:
        traits_text = " • ".join(highlights[:4])  # Limit to 4 highlights
        post_parts.append(f"Key traits: {traits_text}")
        post_parts.append("")
    
    # Quick stats
    stats = []
    stats.append(f"Energy: {energy}/5")
    stats.append(f"Trainability: {trainability}/5")
    if good_with_kids >= 3:
        stats.append(f"Kid-friendly: {good_with_kids}/5")
    
    post_parts.append(" | ".join(stats))
    post_parts.append("")
    
    # Call to action
    post_parts.append("Ready to welcome this pup into my life! 🏠")
    post_parts.append("")
    
    # Hashtags
    breed_hashtag = breed_name.replace(" ", "").replace("(", "").replace(")", "")
    hashtags = [
        f"#{breed_hashtag}",
        "#DogMatchmaker",
        "#FindYourPerfectDog",
        "#DogBreed",
        "#PetMatch",
        "#DogLovers"
    ]
    post_parts.append(" ".join(hashtags))
    
    return "\n".join(post_parts)

