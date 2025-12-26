"""
Docu-chan - AI Documentation Generator

目前只實作 Phase 3: Chart Generation Loop

Usage:
    python main.py --chart "<description>"
"""
import sys
import argparse
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import load_config
from agents.context import AgentContext
from agents import ChartLoop


def main():
    """Main entry point for the documentation generator."""
    parser = argparse.ArgumentParser(description="Docu-chan - AI Documentation Generator")
    parser.add_argument("--chart", type=str, help="Generate a chart from description")
    parser.add_argument("--output", "-o", type=str, default="outputs/final/diagrams", help="Output directory")
    parser.add_argument("--skip-inspection", action="store_true", help="Skip visual inspection")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max revision iterations")
    args = parser.parse_args()
    
    print("=" * 50)
    print("  Docu-chan v0.3.0")
    print("  AI Documentation Generator")
    print("  (Phase 3: Chart Generation)")
    print("=" * 50)
    
    # 載入設定並初始化共用 Context
    try:
        config = load_config()
        AgentContext.initialize(
            api_key=config.api_key,
            base_url=config.api_base_url
        )
    except Exception as e:
        print(f"\n[Error] Failed to initialize: {e}")
        print("Please set API_KEY and API_BASE_URL in .env file")
        return 1
    
    # Chart mode
    if args.chart:
        print(f"\n[Chart Mode] Generating chart...")
        print(f"Request: {args.chart}")
        
        chart_loop = ChartLoop(
            log_dir=str(config.chart.log_dir),
            output_dir=str(config.chart.output_dir) if not args.output else args.output,
            designer_model=config.models.diagram_designer,
            coder_model=config.models.mermaid_coder,
            evaluator_model=config.models.visual_inspector
        )
        result = chart_loop.run(
            args.chart, 
            skip_inspection=args.skip_inspection
        )
        
        if result.success:
            print(f"\n✓ Chart saved to: {result.image_path}")
            if result.mermaid_code:
                print(f"  Diagram type: {result.mermaid_code.diagram_type}")
                print(f"  Iterations: {result.iterations}")
        else:
            print(f"\n✗ Failed: {result.error}")
        return 0 if result.success else 1
    
    # Show usage
    print("\nUsage:")
    print("  python main.py --chart '<description>'")
    print("")
    print("Options:")
    print("  --output, -o          Output directory (default: outputs/final/diagrams)")
    print("  --skip-inspection     Skip visual quality inspection")
    print("  --max-iterations N    Max revision iterations (default: 5)")
    print("")
    print("Examples:")
    print("  python main.py --chart 'User login authentication flow'")
    print("  python main.py --chart 'System architecture diagram' -o ./diagrams")
    print("  python main.py --chart 'Database ER diagram' --skip-inspection")
    print("")
    print("Note: Phase 1, 2, 4 are not yet implemented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
