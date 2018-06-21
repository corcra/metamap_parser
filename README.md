# metamap parser
A python script for parsing the JSON output of the NLM MetaMap

## What is MetaMap?

[MetaMap - A Tool For Recognizing UMLS Concepts in Text](https://metamap.nlm.nih.gov/)
[UMLS: Unified Medical Language System](https://www.nlm.nih.gov/research/umls/)

Basically, it takes free text and identifies UMLS concepts in that text. These concepts are identified using CUIs - concept unique identifiers.

## What does the script do?

It finds mentions of CUIs in the JSON output of MetaMap, and inserts them back into the original document, replacing the parts of the string that MetaMap identified as mapping to that CUI.

### Examples

Input sentence: `It does not impede her lifestyle at this point` --> `It does C1518422 impede her C0023676 at this C1552961`

#### Negation:
If MetaMap has flagged that the CUI is negated, it will be replace as `NOTCUI`, e.g.
`No rashes` -- > `No NOTC0015230`

#### Remapping:
The script also creates a "remapped" version, where the CUI is translated back into its preferred string form, e.g.:
`Sclerae white` --> `C0036410 C0007457` --> `SCLERA WHITE`

This is largely for sanity-checking the parsing and occasionally breaks sentence structure, but could in principle be used to reduce sentence variability.

## Usage

Assuming a python(3) interactive session, run `process_document(path_in, path_out)`, where `path_in` is the path to the MetaMap JSON output file, and `path_out` is optionally the desired path to write to.
If you don't provide `path_out` it will just write to `path_in` + `".parsed"`

## Assumptions

I hacked this together using somewhat limited documentation, so I make the following assumptions:

1. We take the first utterance in the list of `Utterances`
1. We take the first mapping in the list of `Mappings`
2. If a concept maps to multiple places in a string, we put the CUI replacement at the first part (e.g. `infection of the lung` --> `LUNGINFECTION of the` because `infection` and `lung` are both part of the CUI, so we just replace `infection` with the whole CUI (which I am pretending is `LUNGINFECTION`)
