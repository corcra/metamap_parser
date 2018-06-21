#!/usr/bin/env ipython
# parse the JSON output of metamap
# This was developed using this MetaMap and options:

# metamap --sldi --JSONn
#/opt/public_mm/bin/SKRrun.16 /opt/public_mm/bin/metamap16.BINARY.Linux --lexicon db -Z 2016AA --sldi --JSONn
#Berkeley DB databases (USAbase 2016AA strict model) are open.
#Static variants will come from table varsan in /opt/public_mm/DB/DB.USAbase.2016AA.strict.
#Derivational Variants: Adj/noun ONLY.
#Variant generation mode: static.
#{"AllDocuments":[Established connection $stream(47132202841296) to TAGGER Server on localhost.
#
#metamap16.BINARY.Linux (2016)
#
#Control options:
#  composite_phrases=4
#  lexicon=db
#  mm_data_year=2016AA
#  sldi
#  JSONn

import json
import ipdb
import paths
import glob
import pandas as pd
import numpy as np
import json
import os

def parse_phrase(phrase, utterance, verbose=True):
    """
    """
    phrase_text = phrase['PhraseText']
    if verbose: print('Parsing phrase', phrase_text)
    mappings = phrase['Mappings']
    CUIs = []
    CUI_strings = []
    starts = []
    lengths = []
    if len(mappings) == 0:
        # no mappings, no parsing
        pass
    else:
        mapping = mappings[0]
        # we take the first mapping (it's the best according to metamap)
        candidates = mapping['MappingCandidates']
        for candidate in candidates:
            # get the candidate, starts, ends
            candidate_CUI = candidate['CandidateCUI']
            CUI_string = candidate['CandidateMatched']
            # if there is more than one conceptPI it means it maps to two places in the string
            # e.g. its split up across multiple words/segments
            for (pi_idx, concept_position_information) in enumerate(candidate['ConceptPIs']):
                candidate_start = concept_position_information['StartPos']
                candidate_length = concept_position_information['Length']
                if pi_idx > 0:
                    # we only retain the first instance, all other replacements are empty
                    this_candidate_CUI = ''
                    this_CUI_string = ''
                else:
                    if (candidate['Negated'] == '1'):
                        this_candidate_CUI = 'NOT' + candidate_CUI
                        this_CUI_string = 'NOT' + CUI_string
                    else:
                        this_candidate_CUI = candidate_CUI
                        this_CUI_string = CUI_string
                CUI_strings.append(this_CUI_string)
                CUIs.append(this_candidate_CUI)
                starts.append(int(candidate_start))
                lengths.append(int(candidate_length))
    assert len(CUIs) == len(starts)
    assert len(starts) == len(lengths)
    assert len(lengths) == len(CUI_strings)
    return CUIs, starts, lengths, CUI_strings

def test_replace_sections_of_string():
    """
    """
    input_string = 'hello world'
    # example 1
    replacements = ['12', '3']
    starts = [0, 5]
    lengths = [2, 4]
    expected_string = '12llo3ld'
    output_string = replace_sections_of_string(input_string, replacements, starts, lengths)
    assert output_string == expected_string
    print('Example 1 passed')
    # example 2
    replacements = ['AAAA', 'BB', 'C']
    starts = [1, 6, 10]
    lengths = [3, 2, 1]
    expected_string = 'hAAAAo BBrlC'
    output_string = replace_sections_of_string(input_string, replacements, starts, lengths)
    assert output_string == expected_string
    print('Example 2 passed')
    # example 3
    replacements = ['0000']
    starts = [2]
    lengths = [4]
    expected_string = 'he0000world'
    output_string = replace_sections_of_string(input_string, replacements, starts, lengths)
    assert output_string == expected_string
    print('Example 3 passed')
    # example 4
    replacements = []
    starts = []
    lengths = []
    expected_string = 'hello world'
    output_string = replace_sections_of_string(input_string, replacements, starts, lengths)
    assert output_string == expected_string
    print('Example 4 passed')
    # example 5 (the same as 2 but given in the wrong order)
    replacements = ['AAAA', 'C', 'BB']
    starts = [1, 10, 6]
    lengths = [3, 1, 2]
    expected_string = 'hAAAAo BBrlC'
    output_string = replace_sections_of_string(input_string, replacements, starts, lengths)
    assert output_string == expected_string
    print('Example 5 passed')

def replace_sections_of_string(string, replacements, starts, lengths):
    """
    Replace sections of a string (marked by start positions and lengths) with replacement words.
    """
    try:
        assert len(replacements) == len(starts)
        assert len(starts) == len(lengths)
    except AssertionError:
        ipdb.set_trace()
    pieces = len(replacements)
    if pieces == 0:
        # nothing to do
        return string
    try:
        assert max(starts) < len(string)
        assert starts[np.argmax(starts)] + lengths[np.argmax(starts)] <= len(string)
    except AssertionError:
        ipdb.set_trace()
    # we need to sort everything now
    df = pd.DataFrame({'starts': starts, 'lengths': lengths, 'replacements': replacements})
    df.sort_values(by='starts', inplace=True)
    del starts
    del replacements
    del lengths
    # start it, then build it up sequentially
    new_string = string[:df.starts.iloc[0]]
    for n in range(1, pieces + 1):
        replacement = df.replacements.iloc[n-1]
        new_string += replacement
        if n == pieces:
            new_string += string[(df.starts.iloc[n-1] + df.lengths.iloc[n-1]):]
        else:
            new_string += string[(df.starts.iloc[n-1] + df.lengths.iloc[n-1]):df.starts.iloc[n]]
    return new_string

def parse_utterance(utterance, verbose=True):
    if verbose: print('Processing utterance:', utterance['UttText'])
    CUIs, starts, lengths, CUI_strings = [], [], [], []
    utterance_text = utterance['UttText']
    for phrase in utterance['Phrases']:
        # the issue is that the start is given relative to the start of the utterance...
        phrase_CUIs, phrase_starts, phrase_lengths, phrase_CUI_strings = parse_phrase(phrase, utterance_text, verbose)
        CUIs.extend(phrase_CUIs)
        starts.extend(phrase_starts)
        lengths.extend(phrase_lengths)
        CUI_strings.extend(phrase_CUI_strings)
    # now we cut up the utterance
    assert len(CUIs) == len(starts)
    assert len(starts) == len(lengths)
    if len(CUIs) == 0:
        parsed_utterance = utterance_text
        remapped_utterance = utterance_text
    else:
        parsed_utterance = replace_sections_of_string(utterance_text, CUIs, starts, lengths)
        remapped_utterance = replace_sections_of_string(utterance_text, CUI_strings, starts, lengths)
    return parsed_utterance, remapped_utterance

def process_document(path_in, path_out=None, verbose=True):
    if path_out is None:
        path_out = path_in + '.parsed'
        print('No outpath given, writing to', path_out)
    path_out_remapped = path_in + '.remapped'
    print('Writing remapped file to', path_out_remapped)
    
    file_out = open(path_out, 'w')
    file_out_remapped = open(path_out_remapped, 'w')
    
    documents = json.load(open(path_in))['AllDocuments']
    for document_dict in documents:
        document = document_dict['Document']
        # could extract negations at this point
        utterances = document['Utterances']
        if len(utterances) > 1:
            print('WARNING: document has more than one utterance - taking the first one')
        utterance = utterances[0]
        parsed_utterance, remapped_utterance = parse_utterance(utterance, verbose)
        file_out.write(str(parsed_utterance) + '\n')
        file_out_remapped.write(str(remapped_utterance) + '\n')
