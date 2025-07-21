import re
import json
import argparse

def extract_params(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    strategy_name_match = re.search(r'public class (\w+) : Strategy', content)
    strategy_name = strategy_name_match.group(1) if strategy_name_match else "UnknownStrategy"

    parameters = {}
    # This regex is a simplified parser for properties with a [NinjaScriptProperty] attribute.
    # It looks for a property declaration and tries to find a default value in the getter.
    pattern = re.compile(
        r'\[NinjaScriptProperty\]\s*'
        r'(?:\[.*?\]\s*)*'  # Optional other attributes
        r'public\s+(?P<type>\w+)\s+(?P<name>\w+)\s*'
        r'{\s*get;\s*set;\s*}\s*'
        r'(?:public override void OnStateChange\(\)\s*{[^}]*?set\s*\{\s*(?P<name2>\w+)\s*=\s*(?P<value>.*?);)?"',
        re.DOTALL
    )

    # A simpler regex that just gets the property name and type
    pattern_simple = re.compile(r'\[NinjaScriptProperty\]\s*.*?public\s+(?P<type>\w+)\s+(?P<name>\w+)\s*\{ get; set; \}')


    for match in pattern_simple.finditer(content):
        param_name = match.group('name')
        param_type = match.group('type')
        # This is a very simplified default value extraction.
        # A proper parser would be needed for more complex scenarios.
        default_value_match = re.search(f'{param_name}\s*=\s*(.*?);', content)
        default_value = default_value_match.group(1) if default_value_match else None
        parameters[param_name] = default_value


    metadata = {
        "strategyName": strategy_name,
        "parameters": parameters
    }

    return metadata

def main():
    parser = argparse.ArgumentParser(description="Extract parameters from a NinjaTrader strategy file.")
    parser.add_argument("input", help="Path to the input NinjaTrader C# strategy file.")
    parser.add_argument("--output", default="strategy_metadata.json", help="Path to the output JSON file.")
    args = parser.parse_args()

    metadata = extract_params(args.input)

    with open(args.output, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Strategy metadata saved to {args.output}")

if __name__ == "__main__":
    main()
