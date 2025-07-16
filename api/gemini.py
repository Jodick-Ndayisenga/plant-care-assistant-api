from django.conf import settings
import google.generativeai as genai


geminiKey = settings.GEMINI_API_KEY

if not geminiKey:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")


genai.configure(api_key=geminiKey)

system_message = """
Vous êtes Rumenyi, un assistant agricole numérique multilingue, dédié à autonomiser les petits exploitants agricoles.

Votre mission principale est de fournir des conseils agronomiques personnalisés, précis et opportuns. Vous aidez les agriculteurs à :
- prédire et gérer les maladies des plantes (en particulier le mildiou de la pomme de terre),
- diagnostiquer les carences du sol,
- recommander les cultures et les engrais les plus adaptés.

Vous communiquez de manière claire, bienveillante et accessible, notamment en langues locales telles que le kirundi, le français et le swahili.  
Votre objectif est de combler les lacunes en matière d’information, tout en tenant compte des défis liés à la variabilité climatique, à la pauvreté des sols et à l’accès limité aux ressources.

Concentrez-vous toujours sur des conseils pratiques, réalisables et adaptés au contexte local, afin d’augmenter la productivité, améliorer les rendements et soutenir la sécurité alimentaire.
"""


DEFAULT_MODEL_NAME = "gemini-2.5-flash"

async def get_gemini_response(
    user_message: str,
    chat_history: list = None,
    model_name: str = DEFAULT_MODEL_NAME,
) -> str:
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_message
        )

        chat = model.start_chat(history=chat_history if chat_history else [])

        response_stream = await chat.send_message_async(user_message, stream=True)

        full_response_text = ""
        async for chunk in response_stream:
            if chunk.text:
                full_response_text += chunk.text

        if not full_response_text:
            print(f"Warning: Gemini API returned an empty response for: '{user_message}'")
            return "Désolé, je n'ai pas pu générer de réponse pour le moment. Veuillez réessayer."

        return full_response_text

    except Exception as e:
        error_message = f"Erreur lors de la communication avec l'API Gemini : {e}"
        print(error_message)
        raise Exception(error_message)