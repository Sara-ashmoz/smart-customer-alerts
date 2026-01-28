import base64
import re
import anthropic


with open('.anthropickey') as f:
    api_key = f.read().strip()
    client = anthropic.Anthropic(api_key=api_key)


def clean_yaml_content(content):
    content = re.sub(r'^```yaml\s*', '', content)
    content = re.sub(r'\s*```$', '', content)

    yaml_match = re.search(r'```yaml\s*(.*?)\s*```', content, re.DOTALL)
    if yaml_match:
        return yaml_match.group(1)

    return content.strip()



pdf_path = 'path/to/your/document.pdf'

with open(pdf_path, "rb") as f:
    pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                },
                {
                    "type": "text",
                    "text": f"""
                      Please extract: invoice id, title, date, net amount, vat amount, currency, vat percentage, total amount.
                      Notes:
                      - output a YAML format ONLY, without any additional text. 
                      - The title should be one word, e.g. arnona, zoom, github, fuel, bezeq, aws, bookkeeper, electricity, equipment, office, phone, train, parking, kvish6, etc.
                      - The currency must be sign, e.g. $, ₪, etc.
                      - The date must be in format YYYY-MM-DD (the year should be 2026). Hebrew invoices dates are usually European date format (DD/MM/YYYY).
                      - Prices without the currency sign, only numbers.
                      -  Do not add any other entries except what you was tasked to.
                    """
                }
            ]
        }
    ],
)



yaml_content = clean_yaml_content(message.content[0].text)