# Act Commands for Local Testing

## Prerequisites

Install act if not already installed:
```bash
brew install act
```

## Available Commands

### 1. List all workflows
```bash
act -l
```

### 2. Test Code Quality workflow
```bash
# Run the entire code quality workflow
act -W .github/workflows/code-quality.yml

# Run specific job only
act -W .github/workflows/code-quality.yml -j lint
act -W .github/workflows/code-quality.yml -j spellcheck
act -W .github/workflows/code-quality.yml -j markdown-lint
```

### 3. Test Docker Build workflow (lightweight tests)
```bash
# Run only the test job (fastest)
act -W .github/workflows/docker-build-test.yml -j test

# Run docker build test for specific font style
act -W .github/workflows/docker-build-test.yml -j docker-build --matrix font-style:han_serif
act -W .github/workflows/docker-build-test.yml -j docker-build --matrix font-style:handwritten

# Run performance benchmarks
act -W .github/workflows/docker-build-test.yml -j performance-test
```

### 4. Simulate different events

#### Pull Request event
```bash
act pull_request -W .github/workflows/docker-build-test.yml -j test
act pull_request -W .github/workflows/code-quality.yml
```

#### Push to master (integration test)
```bash
act push -W .github/workflows/docker-build-test.yml -j integration-test --eventpath .github/events/push-master.json
```

### 5. Dry run (show what would run)
```bash
act -n -W .github/workflows/docker-build-test.yml
act -n -W .github/workflows/code-quality.yml
```

### 6. Run with secrets (if needed)
```bash
act -W .github/workflows/docker-build-test.yml --secret-file .secrets
```

### 7. Debug mode
```bash
act -W .github/workflows/code-quality.yml -j lint --verbose
```

## Event Files for Testing

Create event files to simulate specific GitHub events:

### Push to master event
```bash
mkdir -p .github/events
cat > .github/events/push-master.json << 'EOF'
{
  "ref": "refs/heads/master",
  "repository": {
    "name": "Mengshen-pinyin-font",
    "full_name": "user/Mengshen-pinyin-font"
  }
}
EOF
```

### Pull request event
```bash
cat > .github/events/pull-request.json << 'EOF'
{
  "pull_request": {
    "head": {
      "ref": "feat/test-branch"
    },
    "base": {
      "ref": "master"
    }
  }
}
EOF
```

## Quick Test Commands

### Fast development workflow test
```bash
# Quick code quality check (fastest)
act -W .github/workflows/code-quality.yml -j lint

# Quick unit tests only
act -W .github/workflows/docker-build-test.yml -j test
```

### Full local CI simulation
```bash
# Run both workflows in sequence
act -W .github/workflows/code-quality.yml && \
act -W .github/workflows/docker-build-test.yml -j test
```

## Notes

- Use `-n` flag for dry runs to see what would execute
- Use `--verbose` for detailed output
- Docker build tests may take significant time - consider running individual jobs
- Integration tests are heavy and may timeout locally
- Some GitHub-specific features (like artifact uploads) may not work perfectly in act

## Troubleshooting

If you encounter issues:

1. **Docker space**: Clean up Docker images
   ```bash
   docker system prune -a
   ```

2. **Memory issues**: Increase Docker memory allocation in Docker Desktop

3. **Platform issues**: Ensure `.actrc` has correct platform mappings

4. **Permission issues**: Check Docker permissions and file ownership