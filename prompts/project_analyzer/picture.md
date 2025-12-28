You are a senior software architect and technical documentation expert.
I will provide an image from a code repository (this could be an architecture diagram, flowchart, UI screenshot, or ER diagram).
Please analyze this image and generate a structured technical analysis report for use in writing the README or development documentation.
Please strictly adhere to the following Markdown output format:

## 1. Image Type
Determine the image type (e.g., System Architecture Diagram, Sequence Diagram, UI Screenshot, ER Diagram, Cloud Infrastructure).

## 2. High-Level Summary
Briefly describe the system functionality or business logic represented by this diagram in 1-2 sentences.

## 3. Key Components & Labels
List all visible text labels, button names, or database fields in the diagram.

* [Component Name/Text]: [Inferred Function or Role]

## 4. Flow & Interactions
If the diagram contains arrows or sequences, please describe the data flow or user action steps in detail.

* Step 1: ...

* Step 2: ...

## 5. Technical Inference
Infer the technology stack used based on the diagram (e.g., seeing AWS in the diagram infers a cloud architecture, seeing React syntax infers a front-end).
Please note:
- Maintain objectivity and accuracy.
- If there are code snippets in the image, try to extract keywords.
- Do not include unnecessary introductory text; directly output the Markdown content.