# Cross-Repo Architecture Reconnaissance

When a user references "mobile files", "native code", "packaging", or platform-specific artifacts in a project, **do not assume they exist in the named repo**. Follow this checklist:

## Trigger Signals
- User asks about Capacitor/Cordova/Expo/native packaging for a web project
- User says "should have mobile files" or "rebase the branch with packaged code"
- User references Android/iOS build artifacts, signing configs, or store submissions
- Project has PWA features (manifest, SW) and user asks about native app

## Recon Steps

1. **Check current repo first**: `git ls-tree -r --name-only <branch> | grep -E "^(android|ios|capacitor|expo|cordova)"`
2. **Search all branches**: loop `git branch -r` checking file trees for native dirs
3. **Search git history**: `git log --all --diff-filter=A --name-only -- "android/*" "ios/*" "*capacitor*"`
4. **Search commit messages**: `git log --all --oneline | grep -iE "capacitor|native|android|ios|packag|打包"`
5. **Scan sibling repos in workspace**: `find ~/Desktop/folder/work -maxdepth 1 -type d` and check each for android/ios/capacitor.config/Podfile/pubspec.yaml
6. **Check for alternative tech stacks**: Flutter (pubspec.yaml, lib/*.dart), React Native (metro.config.js, ios/*.xcodeproj), native Java/Kotlin (build.gradle, AndroidManifest.xml)
7. **Report findings with tech stack identification** — do not assume the mobile app uses the same framework as the web app

## Common Pitfalls

- Assuming web project's "mobile" means Capacitor wrapper of same codebase
- Missing that the mobile app is a completely separate project with different tech stack
- Not checking internal GitLab/GitHub remotes for related repos
- Treating "has android/" as proof of Capacitor (could be Flutter, React Native, or pure native)

## Reporting Template

```
Project: <name>
Current branch: <branch>
Mobile files in this repo: YES/NO
  - android/: present/absent
  - ios/: present/absent
  - capacitor.config.*: present/absent

Sibling mobile projects found:
  - <path>: <tech_stack> (<package_name/bundle_id>)
  - <path>: <tech_stack> (<package_name/bundle_id>)

Code reuse analysis:
  - Shared code: <list or "none — completely independent">
  - Overlapping business modules: <list>
```
