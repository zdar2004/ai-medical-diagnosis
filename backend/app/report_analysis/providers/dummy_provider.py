class DummyProvider:
    """
    Temporary provider for testing the report analysis pipeline.
    """

    def generate(self, prompt: str) -> str:
        return (
            "Laboratory analysis reveals abnormalities outside the reference "
            "range. Physician review is recommended. This summary is for "
            "informational purposes only and does not represent a diagnosis."
        )