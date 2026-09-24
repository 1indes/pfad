# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""A blocking input call pauses this execution path until you answer."""

print("Before input: the next line waits for you.")
name = input("Name? ")
print("Hello", name)
print("After input: this line could only run after your answer.")
