Markov chain based procedural poetry generator.

Installation:
  1. If you don't have it, install Python 3 using your system's package
     manager. OS X - `brew install python3`
  2. Clone the repository into a folder on your computer.
  3. Install the required packages - `pip3 install -r requirements.txt`

Use:
  I've included a crude command-line application which you can use to
  generate lines according to a rhyme scheme and print them to the
  console constantly until you terminate it with C-c. Use it like this:
  `./app --corpus a_folder --scheme aabb --nwords 4`
  The argument to `--corpus` should be a folder containing text files,
  to `--scheme` a rhyme scheme, and to `--nwords` the length of the
  lines you want to generate.

Enjoy