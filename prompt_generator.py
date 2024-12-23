import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM
import matplotlib.pyplot as plt
# Load lightweight models
models = {
    "DistilGPT-2": "distilgpt2",  # A smaller version of GPT-2 with less memory usage
    "GPT-Neo-125M": "EleutherAI/gpt-neo-125M"  # Smaller version of GPT-Neo, fast and lightweight
}
# Initialize models and tokenizers with padding token set
model_tokenizers = {name: AutoTokenizer.from_pretrained(model_path) for name, model_path in models.items()}
# Ensure pad_token is set (using eos_token as pad_token)
for tokenizer in model_tokenizers.values():
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token  # Assign EOS token as padding token
model_objects = {name: AutoModelForCausalLM.from_pretrained(model_path).to("cpu") for name, model_path in models.items()}
# Function to generate prompts using a specific model
def generate_prompt_with_model(model_name, description, modality, condition, details, max_length=100):
    base_prompt = f"Generate a {modality} scan of {description}. Focus on the medical imaging context only."
    if condition:
        base_prompt += f" Focus on capturing {condition}."
    if details:
        base_prompt += f" Include details such as {details}."
    base_prompt += " Avoid any extra information, references, or irrelevant content. Keep the prompt focused only on the image generation task."
    # Tokenize input and generate output
    tokenizer = model_tokenizers[model_name]
    model = model_objects[model_name]
    inputs = tokenizer(base_prompt, return_tensors="pt", padding=True, truncation=True, max_length=max_length)
    inputs = inputs.to("cpu")
    # Adjust generation settings
    output = model.generate(
        inputs["input_ids"], 
        max_length=max_length, 
        temperature=0.7,  # Apply temperature if sampling
        do_sample=True,   # Enable sampling to use temperature
        top_p=0.9,        # Optionally use nucleus sampling (can adjust as needed)
        pad_token_id=model.config.pad_token_id  # Ensure pad_token_id is set
    )
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    return generated_text.strip()
# Function to evaluate the quality of the prompt
def evaluate_prompt(prompt):
    # Basic scoring based on length and clarity (could be enhanced with NLP metrics like BLEU, ROUGE, etc.)
    length_score = len(prompt.split())
    clarity_score = len([word for word in prompt.split() if len(word) > 3])  # Basic metric for clarity (words > 3 chars)
    
    # Combine these scores to get a final score (you can adjust weights as needed)
    final_score = length_score + clarity_score
    return length_score, clarity_score, final_score
# Streamlit App GUI
st.set_page_config(page_title="Multi-Model Medical Prompt Generator", layout="wide")
st.title("Multi-Model Medical Prompt Generator")
st.markdown("By Debojyoti Ghosh")
st.markdown("Generate optimized medical prompts using multiple models and compare the outcomes.")
# Input Parameters
col1, col2 = st.columns(2)
with col1:
    description = st.text_input("Description of Image (e.g., 'human brain')", "")
    modality = st.selectbox("Imaging Modality", ["MRI", "CT", "X-ray", "Ultrasound"])
    condition = st.text_input("Condition to Highlight (optional)", "")
with col2:
    details = st.text_area("Additional Details (optional)", "")
    max_length = st.slider("Maximum Length of Generated Prompt", 50, 200, 100)
# Button to Generate Prompt
if st.button("Generate Prompts"):
    with st.spinner("Generating prompts from multiple models..."):
        try:
            results = {}
            model_scores = {}
            length_scores = []
            clarity_scores = []
            # Generate prompts for each model and evaluate them
            for model_name in models.keys():
                output = generate_prompt_with_model(model_name, description, modality, condition, details, max_length)
                results[model_name] = output
                length_score, clarity_score, final_score = evaluate_prompt(output)
                model_scores[model_name] = final_score
                length_scores.append(length_score)
                clarity_scores.append(clarity_score)
            
            # Find the best prompt (highest score)
            best_model = max(model_scores, key=model_scores.get)
            best_prompt = results[best_model]
            # Display the best prompt
            st.success("Best Prompt Generated Successfully!")
            st.subheader(f"Best Prompt Generated by {best_model}")
            st.text_area(f"Best Prompt", best_prompt, height=150)
            # Display comparison metrics
            st.subheader("Comparison Metrics")
            
            # Plotting the comparison metrics
            fig, ax = plt.subplots(figsize=(8, 5))
            model_names = list(models.keys())
            ax.bar(model_names, length_scores, label="Length Score", alpha=0.6)
            ax.bar(model_names, clarity_scores, label="Clarity Score", alpha=0.6)
            ax.set_xlabel('Model')
            ax.set_ylabel('Score')
            ax.set_title('Comparison of Prompt Length and Clarity Scores')
            ax.legend()
            # Show plot
            st.pyplot(fig)
            # Display metric values
            for model_name, output in results.items():
                length_score, clarity_score, final_score = evaluate_prompt(output)
                st.markdown(f"### {model_name}")
                st.write(f"**Prompt Length:** {length_score} words")
                st.write(f"**Clarity Score (based on word length):** {clarity_score}")
                st.write(f"**Final Score:** {final_score}")
                st.write(f"**First 10 Words:** {' '.join(output.split()[:10])}")
                
                # Custom comment based on the evaluation
                if final_score < 150:
                    st.write("**Comment:** The generated prompt could be improved by making it more specific and detailed.")
                elif final_score >= 150 and final_score < 200:
                    st.write("**Comment:** The prompt is fairly descriptive, but it could benefit from additional details.")
                else:
                    st.write("**Comment:** The prompt is well-structured and highly descriptive.")
        except Exception as e:
            st.error(f"Error: {e}")
# Footer
st.markdown("---")
st.markdown("© 2024 Multi-Model Prompt Generator | Powered by Open-Source Models")
