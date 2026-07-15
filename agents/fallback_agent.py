import os
import logging

try:
    from google.adk.agents import Agent as ADKAgent
    HAS_ADK = True
except ImportError:
    HAS_ADK = False

class FallbackAgent:
    def __init__(self):
        self.name = "FallbackAgent"
        self.instruction = """
        You are the Fallback Agent of Rythu Mitra AI.
        Your job is to provide support when input is unclear, when a disease cannot be diagnosed, 
        or when weather/scheme details are missing. Suggest contacting local Rythu Bharosa Kendras (RBKs).
        """
        
        if HAS_ADK:
            try:
                self.adk_agent = ADKAgent(
                    name=self.name,
                    instruction=self.instruction,
                    model="gemini-2.5-flash"
                )
            except Exception as e:
                logging.warning(f"Failed to initialize ADK Agent for {self.name}: {e}")
                self.adk_agent = None
        else:
            self.adk_agent = None

    def get_fallback_response(self, lang="te", reason=None):
        """Returns standard, helpful fallback advice when system is uncertain."""
        
        # AP Toll-Free Farmer Helpline number: 155251 / 1902
        helpline = "155251"
        
        if lang == "te":
            message = "క్షమించండి, మీ ప్రశ్న లేదా ఫోటోకు స్పష్టమైన సమాధానాన్ని మేము గుర్తించలేకపోయాము. దయచేసి క్రింది మార్గాలను అనుసరించండి:\n"
            if reason:
                message += f"కారణం: {reason}\n\n"
            message += f"1. మీ గ్రామంలోని రైతు భరోసా కేంద్రం (RBK) లేదా వ్యవసాయ సహాయకుడిని (AEO) కలవండి.\n"
            message += f"2. ప్రభుత్వ ఉచిత రైతు సహాయక నంబర్ కి ఫోన్ చేయండి: {helpline}."
        else:
            message = "We apologize, but we could not confidently process your request or diagnose the issue.\n"
            if reason:
                message += f"Reason: {reason}\n\n"
            message += f"1. Please visit your nearest Rythu Bharosa Kendra (RBK) or consult your local Agricultural Extension Officer (AEO).\n"
            message += f"2. Call the Government Free Farmer Helpline: {helpline}."
            
        return {
            "message": message,
            "rbk_helpline": helpline,
            "rbk_contact_info": "Rythu Bharosa Kendra (RBK) Help Desk, Andhra Pradesh Department of Agriculture"
        }
