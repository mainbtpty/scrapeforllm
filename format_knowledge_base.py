import json
import re
from datetime import datetime
import os

def clean_text(text):
    """Clean and normalize text content."""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    # Remove duplicate sentences
    sentences = text.split('. ')
    unique_sentences = []
    for sentence in sentences:
        if sentence not in unique_sentences and len(sentence.strip()) > 10:
            unique_sentences.append(sentence)
    
    return '. '.join(unique_sentences)

def extract_activities(content):
    """Extract team building activities from content."""
    activities = {}
    
    # Common activity patterns
    activity_patterns = {
        'Bagel Quiz': r'Bagel Quiz.*?Quiz à l\'humour décalé.*?En savoir plus',
        'City Express': r'City Express.*?parcours digital culturel.*?En savoir plus',
        'Olympia': r'Olympia.*?réflexes, comportements, qualités.*?En savoir plus',
        'Escape Box': r'Escape Box.*?saurez-vous ouvrir le coffre.*?En savoir plus',
        'Green City': r'Green City.*?ville de demain.*?En savoir plus'
    }
    
    for activity, pattern in activity_patterns.items():
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            activities[activity] = clean_text(match.group())
    
    return activities

def extract_testimonials(content):
    """Extract client testimonials from content."""
    testimonials = []
    
    # Pattern to find testimonials (text followed by company name)
    testimonial_pattern = r'([^.]+[.!]+)\s*-\s*([A-Za-z\s&]+)'
    matches = re.findall(testimonial_pattern, content)
    
    for testimonial_text, company in matches:
        if len(testimonial_text.strip()) > 50:  # Only substantial testimonials
            testimonials.append({
                'company': company.strip(),
                'testimonial': clean_text(testimonial_text.strip())
            })
    
    return testimonials

def format_for_ai_knowledge_base(json_data):
    """Convert JSON data to structured knowledge base format."""
    
    if not json_data or len(json_data) == 0:
        return "No data found in JSON file."
    
    # Get the first (main) entry
    main_data = json_data[0]
    
    # Extract key information
    company_name = "Eagles Team Experiences"
    website = main_data.get('url', '')
    title = main_data.get('title', '')
    meta_description = main_data.get('meta_description', '')
    content = main_data.get('main_content', '')
    
    # Extract activities and testimonials
    activities = extract_activities(content)
    testimonials = extract_testimonials(content)
    
    # Build structured knowledge base
    knowledge_base = f"""# {company_name} - Knowledge Base

## Company Overview
**Company Name:** {company_name}
**Website:** {website}
**Specialization:** {title.replace('Eagles Team Experiences - ', '')}
**Description:** {meta_description}
**Experience:** More than 30 years helping teams improve communication and strengthen cohesion
**Location:** Paris, France (with services throughout France)

## Company Mission
To help teams improve their communication and strengthen their cohesion. Whether you want to revive your team's bonds or if you're forming a new team, Eagles Team Experiences is there to help and meet all your needs.

## Core Services
Eagles Team Experiences specializes in creating unique, surprising, playful, original, fantastic, innovative, fun, challenging, creative, musical, cinematic, recreational, amazing, and entertaining team building experiences.

## Best Seller Team Building Activities

"""
    
    # Add activities
    activity_descriptions = {
        'Bagel Quiz': 'Quiz with offbeat humor - Experience a fun team activity with entertaining quiz format',
        'City Express': 'Digital cultural discovery course - Complete a digital cultural and discovery route through Parisian streets',
        'Olympia': 'Team skill development - Learn team reflexes, behaviors, and qualities that contribute to success in all circumstances',
        'Escape Box': 'Team challenge - Work together to open the safe/chest',
        'Green City': 'Creative sustainability challenge - Create the city of tomorrow using imagination, creativity, and social responsibility'
    }
    
    for activity, description in activity_descriptions.items():
        knowledge_base += f"""### {activity}
**Type:** {description.split(' - ')[0]}
**Description:** {description.split(' - ')[1]}
**Benefits:** Team bonding and skill development

"""
    
    # Add service categories
    knowledge_base += """## Service Categories
- **Best Sellers** - Most popular team building activities
- **Surveys and Courses** (Enquêtes et parcours) - Interactive discovery experiences
- **Music and Arts** (Musique et arts) - Creative artistic team activities
- **Challenges** - Problem-solving and competitive team exercises
- **Team Cohesion** (Cohésion d'équipe) - Activities focused on building team unity
- **CSR Activities** (RSE) - Corporate Social Responsibility focused events
- **Gastronomy** - Food and cooking based team experiences
- **Custom Solutions** (Sur-mesure) - Tailored activities for specific needs

## Additional Services
- Team Building activities for all group sizes
- Kick-Off Solutions for new teams
- Outdoor Experiences in natural settings
- Partner Locations throughout France
- Extra Services and add-ons
- Custom Corporate Entertainment solutions

"""
    
    # Add testimonials
    if testimonials:
        knowledge_base += "## Client Testimonials\n\n"
        for testimonial in testimonials[:6]:  # Limit to top 6 testimonials
            knowledge_base += f"""### {testimonial['company']}
"{testimonial['testimonial']}"

"""
    
    # Add business information
    knowledge_base += """## Company Promises
- **Quick Response:** Response in less than 2 hours
- **Dedicated Team:** A team dedicated to its clients
- **Expert Company:** Specialized in corporate entertainment
- **Custom Solutions:** Ability to meet specific client needs
- **Proven Experience:** Over 30 years in team building industry

## Contact Information
- **Website:** https://eagles-team-experiences.com/
- **Phone:** +33 1 74 62 92 64
- **Services:** Available throughout France with focus on Paris
- **Quote Request:** Quick quote available through website contact form
- **Response Time:** Less than 2 hours for inquiries

## Keywords and Tags
team building, corporate events, Paris, France, team experiences, communication, cohesion, corporate entertainment, team activities, professional development, team bonding, custom solutions, outdoor activities, indoor activities, creative challenges, problem solving, employee engagement

## Last Updated
Data extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return knowledge_base

def main():
    """Main function to process the JSON file."""
    input_file = 'eagles_team_data.json'
    output_file = 'eagles_knowledge_base_formatted.txt'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: {input_file} not found!")
        print("Please make sure eagles_team_data.json is in the same directory as this script.")
        return
    
    try:
        # Read JSON file
        print(f"📖 Reading {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Format data
        print("🔄 Processing and formatting data...")
        formatted_content = format_for_ai_knowledge_base(json_data)
        
        # Write formatted output
        print(f"💾 Saving formatted content to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        # Also create a markdown version
        markdown_file = 'eagles_knowledge_base_formatted.md'
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        print("✅ Success! Files created:")
        print(f"   📄 {output_file}")
        print(f"   📄 {markdown_file}")
        print(f"\n📊 Statistics:")
        print(f"   - Characters: {len(formatted_content):,}")
        print(f"   - Words: {len(formatted_content.split()):,}")
        print(f"   - Lines: {len(formatted_content.split(chr(10))):,}")
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Review {output_file} content")
        print(f"   2. Copy content to IntelliWeave AI knowledge base")
        print(f"   3. Use the markdown version for better formatting")
        
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format in {input_file}")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"❌ Error processing file: {e}")

if __name__ == "__main__":
    main()