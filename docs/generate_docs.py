import json
import os


def load_openapi_spec(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_schema(schema, components=None, key=""):
    """Format schema into a readable string."""
    if not schema:
        return "any"

    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return ref_name

    type_ = schema.get("type", "any")

    if type_ == "array":
        items = schema.get("items", {})
        return f"{format_schema(items, components)}[]"

    if type_ == "object":
        if "additionalProperties" in schema:
            return "object"
        return "object"

    format_ = schema.get("format")
    if format_:
        return f"{type_} ({format_})"

    return type_


def get_example_value(schema, prop_name=""):
    """Generate example values based on schema."""
    if not schema:
        return "any"

    if "$ref" in schema:
        return "{...}"

    type_ = schema.get("type", "string")
    format_ = schema.get("format")

    # Check for enum
    if "enum" in schema:
        return f'"{schema["enum"][0]}"'

    if type_ == "string":
        if format_ == "uuid":
            return '"550e8400-e29b-41d4-a716-446655440000"'
        elif format_ == "email":
            return '"user@example.com"'
        elif format_ == "date-time":
            return '"2024-01-01T00:00:00Z"'
        elif "password" in prop_name.lower():
            return '"SecurePassword123!"'
        return f'"{prop_name or "example"}"'
    elif type_ == "integer":
        return "0"
    elif type_ == "number":
        return "0.0"
    elif type_ == "boolean":
        return "true"
    elif type_ == "array":
        return "[]"
    elif type_ == "object":
        return "{}"

    return '""'


def generate_request_example(details, components):
    """Generate curl and JavaScript example for an endpoint."""
    method = details.get("operationId", "").split("_")[0]

    # Get request body schema
    req_body = details.get("requestBody", {})
    body_example = None

    if req_body:
        content = req_body.get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
            if "$ref" in schema:
                ref_name = schema["$ref"].split("/")[-1]
                body_schema = components.get(ref_name, {})
                body_example = generate_schema_example(body_schema, components)
        elif "multipart/form-data" in content:
            body_example = "FormData with file upload"

    return body_example


def generate_schema_example(schema, components):
    """Generate example JSON from schema."""
    if not schema:
        return {}

    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return generate_schema_example(components.get(ref_name, {}), components)

    props = schema.get("properties", {})
    required = schema.get("required", [])

    example = {}
    for prop_name, prop_schema in props.items():
        if prop_name in required or True:  # Include all for demo
            if "$ref" in prop_schema:
                ref_name = prop_schema["$ref"].split("/")[-1]
                ref_schema = components.get(ref_name, {})
                if "enum" in ref_schema:
                    example[prop_name] = ref_schema["enum"][0]
                else:
                    example[prop_name] = "{...}"
            elif "anyOf" in prop_schema:
                # Take first non-null option
                for option in prop_schema["anyOf"]:
                    if option.get("type") != "null":
                        val = get_example_value(option, prop_name)
                        try:
                            example[prop_name] = json.loads(val)
                        except:
                            example[prop_name] = val
                        break
            else:
                val = get_example_value(prop_schema, prop_name)
                try:
                    example[prop_name] = json.loads(val)
                except:
                    example[prop_name] = val

    return example


def generate_mdx(spec):
    mdx = []
    info = spec.get("info", {})
    components = spec.get("components", {}).get("schemas", {})

    # Header with metadata
    mdx.append("---")
    mdx.append(f'title: "{info.get("title", "API Documentation")}"')
    mdx.append(f'description: "Complete API reference for {info.get("title", "API")}"')
    mdx.append("---\n")

    mdx.append(f"# {info.get('title', 'API Documentation')}\n")
    mdx.append(f"> **Version:** {info.get('version', '0.1.0')}\n")

    description = info.get("description")
    if description:
        mdx.append(f"{description}\n")

    # Base URL info
    mdx.append("## Base URL\n")
    mdx.append("```\nhttp://localhost:8000\n```\n")

    mdx.append("## Authentication\n")
    mdx.append("Most endpoints require authentication using Bearer tokens.\n")
    mdx.append("```http\nAuthorization: Bearer YOUR_ACCESS_TOKEN\n```\n")

    # Group by tags
    paths = spec.get("paths", {})
    tags_map = {}

    for path, methods in paths.items():
        for method, details in methods.items():
            tags = details.get("tags", ["Uncategorized"])
            for tag in tags:
                if tag not in tags_map:
                    tags_map[tag] = []
                tags_map[tag].append(
                    {"path": path, "method": method.upper(), "details": details}
                )

    sorted_tags = sorted(tags_map.keys())

    # Generate content by tag
    for tag in sorted_tags:
        mdx.append(f"## {tag}\n")

        endpoints = tags_map[tag]
        for ep in endpoints:
            method = ep["method"]
            path = ep["path"]
            details = ep["details"]
            summary = details.get("summary", "No summary")
            description = details.get("description", "")
            operation_id = details.get("operationId", "")

            mdx.append(f"### {summary}\n")

            # Method and Path badge
            mdx.append(
                f'<div style={{{{display: "flex", gap: "8px", alignItems: "center", marginBottom: "16px"}}}}>'
            )

            colors = {
                "GET": "#61AFFE",
                "POST": "#49CC90",
                "PUT": "#FCA130",
                "PATCH": "#50E3C2",
                "DELETE": "#F93E3E",
            }

            color = colors.get(method, "#999")
            mdx.append(
                f'  <span style={{{{backgroundColor: "{color}", color: "white", padding: "4px 12px", borderRadius: "4px", fontWeight: "bold", fontSize: "12px"}}}}>{{{{ {method} }}}}</span>'
            )
            mdx.append(f"  <code>{path}</code>")
            mdx.append(f"</div>\n")

            if description:
                mdx.append(f"{description}\n")

            # Security requirements
            security = details.get("security", [])
            if security:
                mdx.append(":::info Authentication Required\n")
                mdx.append("This endpoint requires authentication.\n")
                mdx.append(":::\n")

            # Parameters
            params = details.get("parameters", [])
            if params:
                mdx.append("#### Parameters\n")

                # Group by type
                path_params = [p for p in params if p.get("in") == "path"]
                query_params = [p for p in params if p.get("in") == "query"]
                header_params = [p for p in params if p.get("in") == "header"]

                if path_params:
                    mdx.append("**Path Parameters**\n")
                    mdx.append("| Name | Type | Required | Description |")
                    mdx.append("|------|------|----------|-------------|")
                    for p in path_params:
                        name = p.get("name")
                        req = "✅" if p.get("required") else "❌"
                        desc = p.get("description", "")
                        schema = p.get("schema", {})
                        type_ = format_schema(schema, components)
                        mdx.append(f"| `{name}` | `{type_}` | {req} | {desc} |")
                    mdx.append("\n")

                if query_params:
                    mdx.append("**Query Parameters**\n")
                    mdx.append("| Name | Type | Required | Description |")
                    mdx.append("|------|------|----------|-------------|")
                    for p in query_params:
                        name = p.get("name")
                        req = "✅" if p.get("required") else "❌"
                        desc = p.get("description", "")
                        schema = p.get("schema", {})
                        type_ = format_schema(schema, components)
                        default = schema.get("default")
                        if default is not None:
                            desc += f" (default: `{default}`)"
                        mdx.append(f"| `{name}` | `{type_}` | {req} | {desc} |")
                    mdx.append("\n")

                if header_params:
                    mdx.append("**Headers**\n")
                    mdx.append("| Name | Type | Required | Description |")
                    mdx.append("|------|------|----------|-------------|")
                    for p in header_params:
                        name = p.get("name")
                        req = "✅" if p.get("required") else "❌"
                        desc = p.get("description", "")
                        schema = p.get("schema", {})
                        type_ = format_schema(schema, components)
                        mdx.append(f"| `{name}` | `{type_}` | {req} | {desc} |")
                    mdx.append("\n")

            # Request Body
            req_body = details.get("requestBody")
            if req_body:
                content = req_body.get("content", {})
                for content_type, body_details in content.items():
                    mdx.append(f"#### Request Body (`{content_type}`)\n")
                    schema = body_details.get("schema", {})

                    if "$ref" in schema:
                        ref_name = schema["$ref"].split("/")[-1]
                        mdx.append(f"See schema: [`{ref_name}`](#{ref_name.lower()})\n")

                        # Generate example
                        body_schema = components.get(ref_name, {})
                        example = generate_schema_example(body_schema, components)
                        if example:
                            mdx.append("**Example:**\n")
                            mdx.append("```json")
                            mdx.append(json.dumps(example, indent=2))
                            mdx.append("```\n")

            # Code Examples
            mdx.append("#### Example Request\n")

            # Generate curl example
            curl_example = f"curl -X {method} 'http://localhost:8000{path}'"

            if security:
                curl_example += " \\\n  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'"

            # Add path params example
            example_path = path
            for param in [p for p in params if p.get("in") == "path"]:
                param_name = param.get("name")
                schema = param.get("schema", {})
                example_val = get_example_value(schema, param_name).strip('"')
                example_path = example_path.replace(f"{{{param_name}}}", example_val)

            curl_example = f"curl -X {method} 'http://localhost:8000{example_path}'"

            if security:
                curl_example += " \\\n  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN'"

            # Add query params
            query_params = [
                p for p in params if p.get("in") == "query" and p.get("required")
            ]
            if query_params:
                query_parts = []
                for p in query_params[:2]:  # Limit to 2 for readability
                    name = p.get("name")
                    schema = p.get("schema", {})
                    example_val = get_example_value(schema, name).strip('"')
                    query_parts.append(f"{name}={example_val}")
                if query_parts:
                    curl_example = curl_example.replace(
                        "'", f"?{'&'.join(query_parts)}'", 1
                    )

            if req_body:
                curl_example += " \\\n  -H 'Content-Type: application/json'"
                body_example = generate_request_example(details, components)
                if body_example and isinstance(body_example, dict):
                    curl_example += (
                        " \\\n  -d '"
                        + json.dumps(body_example, separators=(",", ":"))
                        + "'"
                    )

            mdx.append("```bash")
            mdx.append(curl_example)
            mdx.append("```\n")

            # JavaScript/Fetch example
            mdx.append("```javascript")
            js_example = (
                f"const response = await fetch('http://localhost:8000{example_path}"
            )

            if query_params:
                query_parts = []
                for p in query_params[:2]:
                    name = p.get("name")
                    schema = p.get("schema", {})
                    example_val = get_example_value(schema, name).strip('"')
                    query_parts.append(f"{name}={example_val}")
                if query_parts:
                    js_example += f"?{'&'.join(query_parts)}"

            js_example += "', {\n"
            js_example += f"  method: '{method}',\n"

            headers = []
            if security:
                headers.append("    'Authorization': 'Bearer YOUR_ACCESS_TOKEN'")
            if req_body:
                headers.append("    'Content-Type': 'application/json'")

            if headers:
                js_example += "  headers: {\n"
                js_example += ",\n".join(headers)
                js_example += "\n  }"

            if req_body:
                body_example = generate_request_example(details, components)
                if body_example and isinstance(body_example, dict):
                    if headers:
                        js_example += ",\n"
                    js_example += (
                        "  body: JSON.stringify("
                        + json.dumps(body_example, indent=4).replace("\n", "\n  ")
                        + ")"
                    )

            js_example += "\n});\n\n"
            js_example += "const data = await response.json();"

            mdx.append(js_example)
            mdx.append("```\n")

            # Responses
            responses = details.get("responses", {})
            if responses:
                mdx.append("#### Responses\n")

                for code, resp in responses.items():
                    desc = resp.get("description", "")
                    mdx.append(f"**{code}** - {desc}\n")

                    content = resp.get("content", {})
                    if "application/json" in content:
                        schema = content["application/json"].get("schema", {})

                        if "$ref" in schema:
                            ref_name = schema["$ref"].split("/")[-1]
                            mdx.append(
                                f"Returns: [`{ref_name}`](#{ref_name.lower()})\n"
                            )
                        elif schema.get("type") == "array":
                            items = schema.get("items", {})
                            if "$ref" in items:
                                ref_name = items["$ref"].split("/")[-1]
                                mdx.append(
                                    f"Returns: Array of [`{ref_name}`](#{ref_name.lower()})\n"
                                )
                    mdx.append("\n")

            mdx.append("---\n\n")

    # Schemas Section
    mdx.append("## Data Schemas\n")
    mdx.append("Complete reference for all data models used in the API.\n\n")

    for name, schema in sorted(components.items()):
        mdx.append(f"### {name}\n")
        mdx.append(f'<a id="{name.lower()}"></a>\n')

        desc = schema.get("description")
        if desc:
            mdx.append(f"{desc}\n")

        # Check if it's an enum
        if "enum" in schema:
            mdx.append(f"**Enum Values:** `{' | '.join(schema['enum'])}`\n\n")
            continue

        props = schema.get("properties", {})
        required = schema.get("required", [])

        if props:
            mdx.append("| Property | Type | Required | Description |")
            mdx.append("|----------|------|----------|-------------|")
            for prop_name, prop_details in props.items():
                type_ = format_schema(prop_details, components)
                req = "✅" if prop_name in required else "❌"
                prop_desc = prop_details.get("description", "")

                # Handle anyOf (nullable fields)
                if "anyOf" in prop_details:
                    types = []
                    for option in prop_details["anyOf"]:
                        if option.get("type") != "null":
                            types.append(format_schema(option, components))
                    type_ = " \\| ".join(types) if types else "any"
                    type_ += " (nullable)"

                # Add default value if present
                default = prop_details.get("default")
                if default is not None:
                    prop_desc += f" Default: `{default}`"

                # Add constraints
                min_val = prop_details.get("minimum")
                max_val = prop_details.get("maximum")
                min_len = prop_details.get("minLength")
                max_len = prop_details.get("maxLength")

                constraints = []
                if min_val is not None:
                    constraints.append(f"min: {min_val}")
                if max_val is not None:
                    constraints.append(f"max: {max_val}")
                if min_len is not None:
                    constraints.append(f"minLength: {min_len}")
                if max_len is not None:
                    constraints.append(f"maxLength: {max_len}")

                if constraints:
                    prop_desc += f" ({', '.join(constraints)})"

                mdx.append(f"| `{prop_name}` | `{type_}` | {req} | {prop_desc} |")
            mdx.append("\n")

            # Add example object
            example = generate_schema_example(schema, components)
            if example:
                mdx.append("**Example:**\n")
                mdx.append("```json")
                mdx.append(json.dumps(example, indent=2))
                mdx.append("```\n")

        mdx.append("\n")

    return "\n".join(mdx)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, "openapi.json")
    output_file = os.path.join(base_dir, "API_REFERENCE.md")

    if os.path.exists(input_file):
        spec = load_openapi_spec(input_file)
        mdx_content = generate_mdx(spec)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(mdx_content)
        print(f"✅ Generated {output_file}")
        print(f"📄 Documentation contains {len(spec.get('paths', {}))} endpoints")
        print(
            f"📦 {len(spec.get('components', {}).get('schemas', {}))} schemas documented"
        )
    else:
        print(f"❌ File not found: {input_file}")
