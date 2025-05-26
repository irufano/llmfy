import base64
from llmfy.llmfypipe.node.node import END, START


class WorkflowVisualizer:
    @staticmethod
    def create_mermaid_diagram(workflow) -> str:
        """Generate Mermaid diagram markdown from workflow."""
        nodes = workflow.nodes
        edges = workflow.edges
        
        # Start building the diagram
        mermaid = [
            "graph TD",
            "    %% Node Styles",
            "    %% Nodes",
        ]
        
        # Add all nodes
        for name, node in nodes.items():
            # Style nodes based on their type
            if name == START:
                mermaid.append(f"    {name}([{name}])")
                # mermaid.append(f"    class {name} start")
            elif name == END:
                mermaid.append(f"    {name}([{name}])")
                # mermaid.append(f"    class {name} end")
            else:
                mermaid.append(f"    {name}({name})")
        
        mermaid.append("    %% Edges")
        
        # Add all edges
        for edge in edges:
            source = edge.source
            
            if edge.condition is None:
                # Simple edges
                for target in edge.targets:
                    mermaid.append(f"    {source} --> {target}")
            else:
                # Conditional edges
                for target in edge.targets:
                    mermaid.append(f"    {source} -.->|condition| {target}")
        
        mermaid.append("style START fill:#777EFE,stroke:#4F54AA,color:white")
        mermaid.append("style END fill:#777EFE,stroke:#4F54AA,color:white")

        return "\n".join(mermaid)

    @staticmethod
    def generate_diagram_url(mermaid_code: str) -> str:
        """Generate URL for Mermaid diagram image."""
        graphbytes = mermaid_code.encode("utf8")
        base64_bytes = base64.urlsafe_b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        return "https://mermaid.ink/img/" + base64_string