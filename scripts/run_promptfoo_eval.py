import subprocess
import sys

def run_promptfoo_eval():
    cmd = [
        sys.executable, '-m', 'promptfoo', 'eval', 'promptfooconfig.yaml',
        '--output', 'promptfoo_results.json'
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print('promptfoo 평가가 완료되었습니다. 결과: promptfoo_results.json')
    except subprocess.CalledProcessError as e:
        print('promptfoo 평가 실패:', e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_promptfoo_eval() 