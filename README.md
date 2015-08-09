# Berkeley Parser Analyser

This software classifies mistakes in the output of parsers.  For a full description of the method, and discussion of results when applied to a range of well known parsers, see:

   [Parser Showdown at the Wall Street Corral: An Empirical Investigation of Error Types in Parser Output](https://aclweb.org/anthology/D/D12/D12-1096.pdf),
   Jonathan K. Kummerfeld, David Hall, James R. Curran, and Dan Klein,
   EMNLP 2012

   [An Empirical Examination of Challenges in Chinese Parsing](https://aclweb.org/anthology/P/P13/P13-2018.pdf),
   Jonathan K. Kummerfeld, Daniel Tse, James R. Curran, and Dan Klein,
   ACL (short) 2013

If you use my code in your own work, please cite the following papers (for
English and Chinese respectively):

```
@InProceedings{Kummerfeld-etal:2012:EMNLP,
  author    = {Jonathan K. Kummerfeld  and  David Hall  and  James R. Curran  and  Dan Klein},
  title     = {Parser Showdown at the Wall Street Corral: An Empirical Investigation of Error Types in Parser Output},
  booktitle = {Proceedings of the 2012 Joint Conference on Empirical Methods in Natural Language Processing and Computational Natural Language Learning},
  address   = {Jeju Island, South Korea},
  month     = {July},
  year      = {2012},
  pages     = {1048--1059},
  software  = {http://code.google.com/p/berkeley-parser-analyser/},
  url       = {http://www.aclweb.org/anthology/D12-1096},
}

@InProceedings{Kummerfeld-etal:2013:ACL,
  author    = {Jonathan K. Kummerfeld  and  Daniel Tse  and  James R. Curran  and  Dan Klein},
  title     = {An Empirical Examination of Challenges in Chinese Parsing},
  booktitle = {Proceedings of the 51st Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)},
  address   = {Sofia, Bulgaria},
  month     = {August},
  year      = {2013},
  pages     = {98--103},
  software  = {http://code.google.com/p/berkeley-parser-analyser/},
  url       = {http://www.aclweb.org/anthology/P13-2018},
}
```

Here is an example of system output (red brackets are extra, blue are missing and yellow are crossing):

![Image of system terminal output](http://www.jkk.name/images/example_analysis_output.png.png)

I am continuing to work on this so if you have questions (or find bugs!) please let me know. Some questions are answered in the <a href='https://code.google.com/p/berkeley-parser-analyser/source/browse/FAQ.txt'>FAQ.txt</a> file. If you can't find an answer there, please mail me.

## Running the System

There are four main programs:

   classify_english.py
     Classify errors in English output
   classify_chinese.py
     Classify errors in Chinese output
   print_coloured_errors.py
     Print errors using colour in a plain text format (red for extra brackets,
     blue for missing brackets, yellow for crossing brackets, and white for
     correct brackets)
   reprint_trees.py
     Reprint a set of trees in a different format (e.g. single line or
     multiline, plain text or latex), edits such as removing traces can also be
     applied

Running each with no arguments will provide help information.  Also see the
sample folders for example runs.  These were generated as follows:

English:
./src/classify_english.py sample_input/english.gold sample_input/english.berkeley sample_output/classified.english.berkeley

Chinese:
./src/classify_chinese.py sample_input/chinese.gold sample_input/chinese.berkeley sample_output/classified.chinese.berkeley

Coloured errors:
./nlp_util/tools/print_coloured_errors.py sample_input/english.gold sample_input/english.berkeley sample_output/coloured_errors.english.berkeley


For the error analysis runs the files produced are:

classified.berkeley.error_counts  -  The errors, their occurence, and the number of
brackets attributed to them (frequency first, then number of brackets
attributed)

classified.berkeley.init_errors  -  A pretty-print presentation of the initial
errors (red indicates extra spans, blue indicates missing spans, and yellow
are missing spans that cross current spans)

classified.berkeley.out  -  The complete output of the classification, including
each step in each path

Log information:
classified.berkeley.log  -  A log of system notes
classified.berkeley.test_trees  -  The test trees
classified.berkeley.gold_trees  -  The gold trees


For the coloured output we recommend viewing files like so:

less -x3 <filename>

That way the trees don't get too wide.  Also, if you are having trouble seeing
the colours, make sure you are using a tool that interprets ANSI escape codes
(http://en.wikipedia.org/wiki/ANSI_escape_code#Support).  Some people have told
me that they needed to use less with the '-R' flag for them to work.

------------------------------------------------------------------------------
  Questions?
------------------------------------------------------------------------------

Contact me!

[my initials] @berkeley.edu 
Where my initials are 'jkk'

Also check for updates to the code at:

https://code.google.com/p/berkeley-parser-analyser/





Copyright (c) 2013, Jonathan K. Kummerfeld
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
- Neither the name of the University of California, Berkeley nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
