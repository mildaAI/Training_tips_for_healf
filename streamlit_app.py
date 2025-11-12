import os
import streamlit as st
from typing import List, Dict, Tuple
from openrouter_client import OpenRouterClient

# Extra deps for connectivity check
import requests
from dotenv import load_dotenv

load_dotenv()

# Updated UI and text for a fresh look
st.set_page_config(
    page_title="AI-Powered Fitness Planner",
    page_icon="🏋️‍♂️",
    layout="wide"
)

st.title("🌟 Your Personalized Fitness Journey")
st.markdown(
    """
    Welcome to the **AI-Powered Fitness Planner**! 🎯
    
    🏋️‍♂️ **Achieve your fitness goals** with tailored exercise plans.
    
    💡 **How it works:**
    - Enter your details and preferences.
    - Let our AI create a personalized weekly plan for you.
    - Stay motivated and track your progress!
    
    🚀 Let's get started!
    """
)


def check_ollima_host(host: str, timeout: float = 3.0) -> Tuple[bool, str]:
    """Try a simple HTTP GET to the provided host. Returns (ok, message).

    We do a plain GET to the host root to detect connection/refused and surface
    helpful troubleshooting info. This is intentionally conservative (no
    assumptions about specific Ollama endpoints).
    """
    try:
        resp = requests.get(host, timeout=timeout)
        return True, f"Reachable: HTTP {resp.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused — is Ollima running? Try `ollima serve`"
    except requests.exceptions.InvalidURL:
        return False, "Invalid host URL. Make sure it starts with http:// or https://"
    except requests.exceptions.Timeout:
        return False, "Connection timed out — check network and host/port"
    except Exception as e:
        return False, f"Error: {e}"


def list_models(host: str, timeout: float = 3.0):
    """Return a list of available model ids from the Ollama HTTP API (/v1/models).

    Returns an empty list on error.
    """
    try:
        resp = requests.get(f"{host.rstrip('/')}/v1/models", timeout=timeout)
        data = resp.json()
        return [m.get('id') for m in data.get('data', []) if 'id' in m]
    except Exception:
        return []


# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ App Settings")
    
    # OpenRouter API Key input
    api_key = st.text_input(
        "🔑 OpenRouter API Key",
        type="password",
        placeholder="Enter your API key",
        help="Your API key is required to connect to the AI models"
    )
    
    # Model selection
    st.subheader("🤖 AI Model Selection")
    model_options = {
        "Qwen3 14B": "qwen/qwen3-14b:free"
    }
    
    selected_model_name = st.selectbox(
        "Choose an AI model",
        options=list(model_options.keys()),
        index=0,  # Default to Qwen3 14B
        help="Select the AI model from available options"
    )
    
    selected_model = model_options[selected_model_name]
    st.info(f"🤖 Using AI Model: **{selected_model}**")

# Main form
st.header("📝 Share Your Fitness Details")

with st.form("user_info_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        # Age input with validation
        age_input = st.text_input(
            "🎂 Your Age",
            placeholder="e.g., 25",
            help="Please enter your age in years"
        )
        
        # Health issues
        health_issues = st.text_area(
            "🩺 Known Health Issues",
            placeholder="e.g., None, or list any conditions",
            help="Tell us about any health conditions we should consider"
        )
    
    with col2:
        # Exercise time
        exercise_time = st.text_input(
            "⏱️ Daily Exercise Time (minutes)",
            placeholder="e.g., 30",
            help="How much time can you dedicate to exercise daily?"
        )
        
        # Fitness goal
        fitness_goal = st.radio(
            "🎯 Your Fitness Goal",
            options=["Lose weight", "Gain muscle"],
            help="Select your primary fitness goal"
        )
    
    # Submit button
    submitted = st.form_submit_button("✨ Generate My Plan", use_container_width=True)

# Process the form
if submitted:
    # Validation
    errors = []
    
    # Check if API key is provided
    if not api_key:
        errors.append("⚠️ Please enter your OpenRouter API key in the sidebar")
    
    # Validate age input
    if not age_input:
        errors.append("⚠️ Please enter your age")
    else:
        try:
            age = int(age_input)
            if age < 1 or age > 120:
                errors.append("⚠️ Please enter a valid age between 1 and 120")
        except ValueError:
            errors.append("⚠️ Age must be a number, not letters or special characters")
    
    # Validate exercise time
    if not exercise_time:
        errors.append("⚠️ Please enter your daily exercise time")
    else:
        try:
            time_minutes = int(exercise_time)
            if time_minutes < 1:
                errors.append("⚠️ Exercise time must be at least 1 minute")
        except ValueError:
            errors.append("⚠️ Exercise time must be a number")
    
    # Display errors or generate plan
    if errors:
        for error in errors:
            st.error(error)
    else:
        # Create the prompt
        prompt = f"""You are a professional Health and Fitness Coach. Based on the following information, create a personalized weekly exercise plan:

- Age: {age} years old
- Known health issues: {health_issues if health_issues else "None"}
- Available daily exercise time: {time_minutes} minutes
- Fitness goal: {fitness_goal}

Please provide:
1. A detailed weekly exercise plan (7 days)
2. Specific exercises for each day
3. Duration and repetitions/sets
4. Any important considerations based on the health information provided
5. Tips for staying motivated and safe

Format the response in a clear, easy-to-follow structure.

Start the response with: 'This is UAB Sveikata health agent speaking.'
End the response with: 'This answer was generated by AI and is not a professional doctor opinion.'"""

        # Generate response
        with st.spinner("🤔 Generating your personalized exercise plan..."):
            try:
                # Initialize OpenRouter client
                client = OpenRouterClient(api_key=api_key)
                
                # Create chat completion
                response = client.chat.create(
                    model=selected_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional Health and Fitness Coach. Provide detailed, safe, and personalized exercise recommendations."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                # Display the response
                st.success("✅ Your personalized exercise plan is ready!")
                st.markdown("---")
                
                # Display the plan in a nice container
                st.markdown("### 📅 Your Weekly Exercise Plan")
                st.markdown(response.choices[0].message.content)
                st.markdown("---")
                st.warning("⚠️ **Disclaimer:** This is AI-generated response and cannot be treated as professional doctor's advice.")
                
                # Option to download the plan
                plan_text = f"""PERSONALIZED EXERCISE PLAN

Age: {age} years
Health Issues: {health_issues if health_issues else "None"}
Daily Exercise Time: {time_minutes} minutes
Goal: {fitness_goal}

{response.choices[0].message.content}

---
DISCLAIMER: This is AI-generated response and cannot be treated as professional doctor's advice.
"""
                
                st.download_button(
                    label="📥 Download Exercise Plan",
                    data=plan_text,
                    file_name="exercise_plan.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ Error generating plan: {str(e)}")
                st.info("💡 Please check your API key and try again. Make sure you have credits in your OpenRouter account.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>💪 Stay healthy, stay strong! Remember to consult with healthcare professionals before starting any new exercise program.</p>
    </div>
    """,
    unsafe_allow_html=True
)