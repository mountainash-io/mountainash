# Release Procedure

This document outlines the process for creating a new release of the mountainash-expressions package.

## Prerequisites

- You have push access to the main repository.
- You have the necessary permissions to create releases on GitHub.
- You have [Hatch](https://hatch.pypa.io/) installed locally.

## Release Process

1. **Update Version**
   - Navigate to `src/mountainash_expressions/__version__.py`
   - Update the `__version__` variable with the new version number
   - Ensure the version number follows the specified CalVer format:
     - Year and month: `YYYYMM`
     - Release candidate: `YYYYMM.0.0`
     - Prod release: `YYYYMM.1.0`
     - Updates to candidate or prod release: `YYYYMM.1.x`
   - Commit this change to the `main` branch

2. **Prepare Release Notes**
   - Document new features, bug fixes, and breaking changes
   - Include examples of new expression system functionality
   - Note any changes to supported backends or logic operations
   - Update CHANGELOG.md if it exists

3. **Run Pre-release Checks**
   ```bash
   # Run full test suite
   hatch run test:test
   
   # Check code quality
   hatch run ruff:check
   hatch run mypy:check
   
   # Validate build
   hatch build
   ```

4. **Push Changes**
   - Push your changes to the `main` branch on GitHub
   - This will trigger the release workflow

5. **Monitor Workflow**
   - Go to the "Actions" tab in the GitHub repository
   - You should see the "Release with SBOMs" workflow running
   - Monitor the workflow for any errors

6. **Verify Release**
   - Once the workflow completes successfully, go to the "Releases" section of the repository
   - You should see a new release created with the version number you specified
   - Verify that the following assets are attached to the release:
     - Wheel file (`mountainash_expressions-{version}-py3-none-any.whl`)
     - Source distribution (`mountainash_expressions-{version}.tar.gz`)
     - Full SBOM (`mountainash-expressions-{version}-sbom-full.xml`)
     - Direct dependencies SBOM (`mountainash-expressions-{version}-sbom-direct.xml`)

7. **Release Branch**
   - The workflow will create a new `release-{version}` branch
   - This branch can be used for any hotfixes if needed

## Hotfix Process

If you need to create a hotfix for an existing release:

1. Check out the release branch for the version you want to hotfix:
   ```bash
   git checkout release-YYYY.MM.1.0
   ```

2. Create a new branch for your hotfix:
   ```bash
   git checkout -b hotfix-YYYY.MM.1.1
   ```

3. Make your changes and update the version in `__version__.py` to `YYYY.MM.1.1`

4. Run targeted tests to validate the fix:
   ```bash
   # Test the specific functionality
   hatch run test:test-target tests/path/to/affected/tests.py
   
   # Run critical expression system tests
   hatch run test:test-target tests/ternary/test_gold_standard_api.py
   ```

5. Commit your changes and push the hotfix branch

6. Create a pull request to merge the hotfix branch into the release branch

7. Once the pull request is merged, the release workflow will be triggered automatically

## Expression System Release Considerations

When releasing changes to the expression system, pay special attention to:

### Breaking Changes
- Changes to public API methods (`eval_is_true`, `eval_is_false`, etc.)
- Modifications to visitor interfaces
- Changes to mathematical logic or truth tables
- Backend compatibility modifications

### Testing Requirements
Before release, ensure comprehensive testing of:

```bash
# Cross-backend compatibility
hatch run test:test-integration

# Mathematical correctness
hatch run test:test-target tests/ternary/test_ternary_mathematics.py

# Performance regression testing
hatch run test:test-performance

# Gold standard API validation
hatch run test:test-target tests/ternary/test_gold_standard_api.py
```

### Documentation Updates
- Update README.md with new features and examples
- Ensure CLAUDE.md reflects any architectural changes
- Update docstrings for modified public methods
- Include migration guides for breaking changes

## Version Numbering

We use [CalVer](https://calver.org/) versioning: `YYYY.MM.MICRO`

### Version Types
- **Release Candidates**: `2025.01.0.0` - Pre-release versions for testing
- **Production Releases**: `2025.01.1.0` - Stable releases for production use
- **Patch Releases**: `2025.01.1.1` - Bug fixes and minor updates

### Version Increment Rules
- **Major Expression Changes**: New month, reset micro (`2025.02.1.0`)
- **Minor Features**: Increment micro (`2025.01.1.1`)
- **Bug Fixes**: Increment micro (`2025.01.1.2`)
- **Hotfixes**: Increment micro on release branch

## Release Notes Template

```markdown
## Mountain Ash Expressions vYYYY.MM.1.0

### New Features
- Added new ternary logic operations
- Enhanced backend compatibility
- Improved expression builder methods

### Bug Fixes  
- Fixed UNKNOWN value handling in edge cases
- Corrected visitor selection for specific backends
- Resolved performance issues in mathematical operations

### Breaking Changes
- **API Change**: Modified signature of `eval_method()`
- **Backend**: Deprecated support for legacy visitor pattern

### Performance Improvements
- 15% faster expression evaluation
- Reduced memory usage for large expressions
- Optimized cross-backend conversion

### Documentation
- Updated usage examples
- Added new real-world scenarios
- Improved API documentation

### Dependencies
- Updated ibis-framework to 10.4.0
- Added support for polars 1.16.0
- Removed deprecated dependencies
```

## Post-Release Tasks

After a successful release:

1. **Update Documentation**
   - Ensure online documentation reflects the new version
   - Update any external references to the package

2. **Announce Release**
   - Update project websites or internal documentation
   - Notify users of any breaking changes

3. **Monitor Issues**
   - Watch for bug reports related to the new release
   - Respond promptly to user feedback

4. **Plan Next Release**
   - Review feature requests and bug reports
   - Plan development priorities for the next version

## Rollback Procedure

If a release needs to be rolled back:

1. **Immediate Action**
   - Mark the problematic release as pre-release on GitHub
   - Document the issues in release notes

2. **Assessment**
   - Determine if the issues can be fixed with a hotfix
   - Or if a full rollback is necessary

3. **Hotfix Path** (preferred)
   - Follow the hotfix process above
   - Release a patch version quickly

4. **Full Rollback** (if necessary)
   - Revert to the previous stable version
   - Create a new release with reverted changes
   - Communicate clearly with users about the rollback

## Notes

- The workflow checks for existing tags and releases. If a tag or release already exists for the version you're trying to release, the workflow will fail.
- The workflow generates two types of Software Bill of Materials (SBOM):
  - Full SBOM: Includes all dependencies (direct and transitive)
  - Direct SBOM: Includes only direct dependencies
- The workflow uses Hatch to manage the build environment and dependencies
- The release process includes checking out several related Mountain Ash repositories for dependency validation

## Troubleshooting

If the release workflow fails:

1. **Check Version Conflicts**
   - Ensure the version number in `__version__.py` is unique and has not been used before
   - Verify no existing tags match the new version

2. **Dependency Issues**
   - Check that all Mountain Ash dependencies are accessible
   - Verify that dependency branches exist or fallback branches are available

3. **Build Failures**
   ```bash
   # Test the build locally
   hatch build
   
   # Check for import issues
   hatch run python -c "import mountainash_expressions; print('Success')"
   ```

4. **Permission Issues**
   - Verify that the necessary secrets and permissions are correctly set up in repository settings
   - Check GitHub Actions permissions for token access

5. **Expression System Issues**
   - Run comprehensive tests to identify system-specific problems
   - Check cross-backend compatibility
   - Validate mathematical operations

For any other issues, please contact the maintainers or create an issue in the repository.