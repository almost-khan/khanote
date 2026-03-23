# khanote.update

Update khanote skills to the latest version.

## Usage

```
/khanote.update $ARGUMENTS
```

## What this does

1. Checks PyPI for the latest khanote version
2. Updates the SSOT skills in `.khanote/skills/`
3. Re-distributes updated skills to all initialized tools
4. Reports what changed

## Example

```
/khanote.update
```
