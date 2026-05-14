import argparse
from src.backend.core.db import init_db
from src.knowledge_base.pipeline import KnowledgeBuildPipeline


def main() -> None:
    init_db()
    parser = argparse.ArgumentParser(description='电网知识库一键构建脚本')
    parser.add_argument('--mode', choices=['incremental', 'full'], default='incremental')
    args = parser.parse_args()

    pipeline = KnowledgeBuildPipeline()
    report = pipeline.run(mode=args.mode)
    print(report)


if __name__ == '__main__':
    main()
