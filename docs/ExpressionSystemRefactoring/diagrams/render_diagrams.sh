#!/bin/bash

# Script to render Mermaid diagrams to PDF
set -e

echo "Rendering Mermaid diagrams to PDF..."

# Convert title page markdown to PDF using pandoc if available, otherwise skip
if command -v pandoc &> /dev/null && command -v pdflatex &> /dev/null; then
    echo "Creating title page PDF..."
    pandoc 0_title_page.md -o 0_title_page.pdf --pdf-engine=pdflatex
    TITLE_PAGE="0_title_page.pdf"
else
    echo "Pandoc or pdflatex not available, skipping title page..."
    TITLE_PAGE=""
fi

# Render all Mermaid diagrams to PDF
echo "Rendering diagram 1: Core Dimensions..."
npx @mermaid-js/mermaid-cli@latest -i 1_core_dimensions.mmd -o 1_core_dimensions.pdf

echo "Rendering diagram 2: Component Binding..."  
npx @mermaid-js/mermaid-cli@latest -i 2_component_binding.mmd -o 2_component_binding.pdf

echo "Rendering diagram 3: Orthogonal Matrix..."
npx @mermaid-js/mermaid-cli@latest -i 3_orthogonal_matrix.mmd -o 3_orthogonal_matrix.pdf

echo "Rendering diagram 4: Compilation Flow..."
npx @mermaid-js/mermaid-cli@latest -i 4_compilation_flow.mmd -o 4_compilation_flow.pdf

echo "Rendering diagram 5: Parameter Binding..."
npx @mermaid-js/mermaid-cli@latest -i 5_parameter_binding.mmd -o 5_parameter_binding.pdf

# Combine all PDFs
echo "Combining PDFs..."
if [ -n "$TITLE_PAGE" ] && [ -f "$TITLE_PAGE" ]; then
    pdfunite $TITLE_PAGE 1_core_dimensions.pdf 2_component_binding.pdf 3_orthogonal_matrix.pdf 4_compilation_flow.pdf 5_parameter_binding.pdf ../orthogonal_architecture_diagrams_complete.pdf
else
    pdfunite 1_core_dimensions.pdf 2_component_binding.pdf 3_orthogonal_matrix.pdf 4_compilation_flow.pdf 5_parameter_binding.pdf ../orthogonal_architecture_diagrams_complete.pdf
fi

echo "Complete! Generated ../orthogonal_architecture_diagrams_complete.pdf"
echo "File size: $(du -h ../orthogonal_architecture_diagrams_complete.pdf | cut -f1)"