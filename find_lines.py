//  Created by Lin Teng on 16/03/2022.

import os
import sys
import time
import re
import yaml
import operator

source_file = "pass_key_cqa_finger"
target_file = "fail_key_cqa_finger"
output_file = "out1_pass_src_findings.log"

similar_regexp = [[r'healthd\s+.*\s+battery\s+.* chg.*', 30, True]]

config_yaml = None
with open("config_find_lines.yaml", "r") as file_yaml:
    config_yaml = yaml.safe_load(file_yaml)

if config_yaml:
    source_file = config_yaml['source_file']
    target_file = config_yaml['target_file']
    output_file = config_yaml['output_file']
    #max_count_of_same_lines = config_yaml['max_count_of_same_lines']
    #delete_when_meet_max_same = config_yaml['delete_when_meet_max_same']
    omit_regexp = config_yaml['omit_regexp']
    same_regexp = config_yaml['same_regexp']
    similar_regexp = config_yaml['similar_regexp']
    cut_regexp = config_yaml['cut_regexp']

# print("global max_count_of_same_lines : " + str(max_count_of_same_lines))
# print("global delete_when_meet_max_same : " + str(delete_when_meet_max_same))


def my_log(info, over_write=False):
    log_string = time.asctime() + " " + info + "\n"
    print(log_string)

    try:
        if over_write:
            with open('compare_log.txt', 'w') as f:
                f.write(log_string)
                f.close()
        else:
            with open('compare_log.txt', 'a+') as f:
                f.write(log_string)
                f.close()
    except Exception as e:
        print('写入错误日志时发生以下错误：\n%s' % e)


def check_args():
    return True


def split_lines_to_keywords(origin_lines):
    lines_made_by_keywords = []
    for line in origin_lines:
        # print(line.rstrip())
        line_keywords = []
        # m = re.search(r".+?\s+\d+\s+\d+\s+(\w)\s+\W*(\S+)\s+(.*)",line)
        m = re.search(r"(.+?)\s+(\d+)\s+(\d+)\s+(\w)\s+(.*)", line)
        if m:
            # print(m.group(1) + "##" + m.group(2) + "##" + m.group(3) + "#" + m.group(4) + "#" + m.group(5))
            line_keywords.append(m.group(1))
            line_keywords.append(m.group(2))
            line_keywords.append(m.group(3))
            line_keywords.append(m.group(4))
            line_keywords.append(m.group(5))
        else:
            line_keywords.append(" ")
            line_keywords.append(" ")
            line_keywords.append(" ")
            line_keywords.append(" ")
            line_keywords.append(" ")
        lines_made_by_keywords.append(line_keywords)
    return lines_made_by_keywords


def find_lines_in_two_files(source_file, target_file, output_file):
    # get current work path

    # print("max_count_of_same_lines : " + str(max_count_of_same_lines))

    my_log(
        "Info : poll lines in " + source_file + ", try to find the same lines in " + target_file + " and write the result to " + output_file + ".")

    dir_path = os.getcwd()
    full_path_source_file = os.path.join(dir_path, source_file)
    full_path_target_file = os.path.join(dir_path, target_file)
    full_path_output_file = os.path.join(dir_path, output_file)

    print(full_path_source_file)
    print(full_path_target_file)
    source_lines = []
    target_lines = []

    try:
        with open(full_path_source_file, 'r+', encoding='utf-8') as read_file:
            source_lines = read_file.readlines()
            read_file.close()
    except Exception as e:
        my_log("error:  reading file: " + full_path_source_file)

    try:
        with open(full_path_target_file, 'r+', encoding='utf-8') as read_file2:
            target_lines = read_file2.readlines()
            read_file2.close()
    except Exception as e:
        my_log("error:  reading file: " + full_path_target_file)

    # omit the source lines and the target lines by the omit_regexp:
    source_lines_omited = omit_lines_by_regexp(source_lines, omit_regexp);
    target_lines_omited = omit_lines_by_regexp(target_lines, omit_regexp);

    # for the source lines , print them
    # split the source lines to : keywords
    source_lines_by_keywords = split_lines_to_keywords(source_lines_omited)
    # for line_keywords in source_lines_by_keywords:
    #     for keyword in line_keywords:
    #         print(keyword + "$$", end="")
    #     print("\n")

    target_lines_by_keywords = split_lines_to_keywords(target_lines_omited)
    # for line_keywords in target_lines_by_keywords:
    #     for keyword in line_keywords:
    #         print(keyword + "$$", end="")
    #     print("\n")

    # create the output lines list
    output_lines = []
    # for each line in source, compare with the target lines
    for source_line_keywords in source_lines_by_keywords:
        # firstly, write source line to temp_output_lines:
        temp_output_lines = []
        output_line_source = ""
        for keyword in source_line_keywords:
            output_line_source += keyword + "  "
        output_line_source += "\n"
        temp_output_lines.append(output_line_source)
        # secondly , find same lines
        sames_result_list, delete_when_meet_max_same_invoked = \
            all_sames_one_source_line_with_target_lines(same_regexp,
                                                        source_line_keywords,
                                                        target_lines_by_keywords)
        if delete_when_meet_max_same_invoked:
            continue
        temp_output_lines.extend(sames_result_list)
        #  not continue, find similar lines
        similars_result_list, delete_when_meet_max_similar_invoked = \
            all_similars_one_source_line_with_target_lines(similar_regexp,
                                                           source_line_keywords,
                                                           target_lines_by_keywords)

        if delete_when_meet_max_similar_invoked:
            continue
        temp_output_lines.extend(similars_result_list)

        if len(temp_output_lines) > 1:
            # at least one line found, save it to output_lines, and go to next for loop
            output_lines.extend(temp_output_lines)
            continue
        # else no line found, try to use cut_regexp
        subs_result_list, delete_when_meet_max_cuts_invoked = \
            all_cuts_one_source_line_with_target_lines(cut_regexp,
                                                       source_line_keywords,
                                                       target_lines_by_keywords)

        if delete_when_meet_max_cuts_invoked:
            continue
        else:
            temp_output_lines.extend(subs_result_list)
            output_lines.extend(temp_output_lines)

        # for regexp in regex_list:
        #     regexp_string, regexp_max, delete_when_meet_max_similar = regexp
        #     temp_output_lines.extend(similar_one_source_line_with_target_lines(source_line_keywords,
        #                                                                        target_lines_by_keywords,
        #                                                                        regexp_string,
        #                                                                        regexp_max))
        # output_lines.extend(temp_output_lines)

    # end for, then write output_lines to file:
    with open(full_path_output_file, 'w') as f:
        for out_line in output_lines:
            f.write(out_line)
        f.close()


def omit_lines_by_regexp(origin_lines, regex_list):
    lines_after_omitting = []
    for one_line in origin_lines:
        if should_omit_the_line(one_line, regex_list):
            continue
        else:
            lines_after_omitting.append(one_line)
    return lines_after_omitting


def should_omit_the_line(one_line, regex_list):
    for regexp in regex_list:
        if re.search(regexp, one_line):
            return True
    return False


def all_sames_one_source_line_with_target_lines(regex_list,
                                                source_line_keywords,
                                                target_lines_by_keywords):
    sames_result_list = []
    for regexp in regex_list:
        prefix_string, regexp_string, regexp_max, delete_when_meet_max_same = regexp
        one_same_output_lines = same_one_source_line_with_target_lines(prefix_string,
                                                                       source_line_keywords,
                                                                       target_lines_by_keywords,
                                                                       regexp_string,
                                                                       regexp_max)
        # Todo, after (.*), should check if the one_same_output_lines contains lines that already in sames_result_list
        # if Yes, should delete them before append them to same_result_list
        if len(one_same_output_lines) >= regexp_max + 1 and delete_when_meet_max_same:
            # +1 is for the first prefix string, for example &&&&&& line
            return [], True
        else:
            sames_result_list.extend(one_same_output_lines)

    return sames_result_list, False

def all_similars_one_source_line_with_target_lines(regex_list,
                                                   source_line_keywords,
                                                   target_lines_by_keywords):
    similars_result_list = []
    for regexp in regex_list:
        prefix_string, regexp_string, regexp_max, delete_when_meet_max_similar = regexp
        one_similar_output_lines = similar_one_source_line_with_target_lines(prefix_string,
                                                                             source_line_keywords,
                                                                             target_lines_by_keywords,
                                                                             regexp_string,
                                                                             regexp_max)
        if len(one_similar_output_lines) >= regexp_max + 1 and delete_when_meet_max_similar:
            # +1 is for the first +++++++++ line
            return [], True
        else:
            similars_result_list.extend(one_similar_output_lines)

    return similars_result_list, False


def all_cuts_one_source_line_with_target_lines(regex_list,
                                               source_line_keywords,
                                               target_lines_by_keywords):
    cuts_result_list = []
    for regexp in regex_list:
        prefix_string, regexp_string, regexp_max, delete_when_meet_max_cut = regexp
        one_cut_output_lines = cut_one_source_line_with_target_lines(prefix_string,
                                                                       source_line_keywords,
                                                                       target_lines_by_keywords,
                                                                       regexp_string,
                                                                       regexp_max)
        # Todo, after (.*), should check if the one_same_output_lines contains lines that already in sames_result_list
        # if Yes, should delete them before append them to same_result_list
        if len(one_cut_output_lines) >= regexp_max + 1 and delete_when_meet_max_cut:
            # +1 is for the first prefix string, for example &&&&&& line
            return [], True
        else:
            cuts_result_list.extend(one_cut_output_lines)

    return cuts_result_list, False


def cut_one_source_line_with_target_lines(prefix_string,
                                           source_line_keywords,
                                           target_lines_by_keywords,
                                           regexp_string,
                                           regexp_max):
    target_cut_lines_list = []
    # that means, cut off the numbers, then compare the two lines
    compare_source = source_line_keywords[4].strip()
    if len(compare_source) < 5:
        # source too short, skip, return []
        return target_cut_lines_list
    #print(regexp_string)
    source_cut = re.sub(regexp_string, '', compare_source)
    print(compare_source)
    print(source_cut)
    if not source_cut:
        return target_cut_lines_list

    for target_line_keywords in target_lines_by_keywords:
        compare_target = target_line_keywords[4].strip()
        target_cut = re.sub(regexp_string, '', compare_target)
        if not target_cut:
            continue
        # else, search is ok
        if source_cut == target_cut:
            # check if the source line and the target line are same one!, if they are same totally, omit, continue
            if operator.eq(source_line_keywords, target_line_keywords):
                continue
            # not same line, but same when compare the (regexp): target_search.groups()
            output_line_target = ""
            for keyword in target_line_keywords:
                # keyword_new = re.sub(r'/aplog.?/Boot\-', './logpa/Boot-', keyword, 1)
                output_line_target += keyword + "  "
            output_line_target += "\n"
            # output_lines.append(output_line_target)
            output_line_target_modified = re.sub(r'^.{12}', '/logpa/Boot-', output_line_target, 1)
            target_cut_lines_list.append(output_line_target_modified)
            # print(output_line_target)
            if regexp_max == len(target_cut_lines_list):
                break
    if len(target_cut_lines_list) > 0:
        target_cut_lines_list.insert(0, prefix_string*150 + regexp_string + "     " + str(regexp_max) + "\n")
    return target_cut_lines_list



def same_one_source_line_with_target_lines(prefix_string,
                                           source_line_keywords,
                                           target_lines_by_keywords,
                                           regexp_string,
                                           regexp_max):
    target_same_lines_list = []
    # start to find the same line
    compare_source = source_line_keywords[4].strip()
    if len(compare_source) < 5:
        # source too short, skip, return []
        return target_same_lines_list
    #print(regexp_string)
    source_search = re.search(regexp_string, compare_source)
    if not source_search:
        return target_same_lines_list
    compare_source_groups = source_search.groups()

    for target_line_keywords in target_lines_by_keywords:
        compare_target = target_line_keywords[4].strip()
        target_search = re.search(regexp_string,compare_target)
        if not target_search:
            continue
        # else, search is ok
        compare_target_groups = target_search.groups()
        if operator.eq(compare_source_groups, compare_target_groups):
            # check if the source line and the target line are same one!, if they are same totally, omit, continue
            if operator.eq(source_line_keywords, target_line_keywords):
                continue
            # not same line, but same when compare the (regexp): target_search.groups()
            output_line_target = ""
            for keyword in target_line_keywords:
                # keyword_new = re.sub(r'/aplog.?/Boot\-', './logpa/Boot-', keyword, 1)
                output_line_target += keyword + "  "
            output_line_target += "\n"
            # output_lines.append(output_line_target)
            output_line_target_modified = re.sub(r'^.{12}', '/logpa/Boot-', output_line_target, 1)
            target_same_lines_list.append(output_line_target_modified)
            # print(output_line_target)
            if regexp_max == len(target_same_lines_list):
                break
    if len(target_same_lines_list) > 0:
        target_same_lines_list.insert(0, prefix_string*150 + regexp_string + "     " + str(regexp_max) + "\n")
    return target_same_lines_list


def similar_one_source_line_with_target_lines(prefix_string,
                                              source_line_keywords,
                                              target_lines_by_keywords,
                                              regexp_string,
                                              regexp_max):
    target_similar_lines_list = []
    # start to find the similar line
    compare_source = source_line_keywords[4].strip()
    if len(compare_source) < 5:
        # source too short, skip, return []
        return target_similar_lines_list
    #print(regexp_string)
    if not re.search(regexp_string, compare_source):
        return target_similar_lines_list

    target_similar_lines_list = []
    for target_line_keywords in target_lines_by_keywords:
        compare_target = target_line_keywords[4].strip()
        if re.search(regexp_string, compare_target):
            # print("&&&&&&&&&&&&&&   " + str(regexp_max))
            # print("Found the same line!")
            # print(compare_source)
            # output_line_target = "FoundCCC"
            output_line_target = ""
            for keyword in target_line_keywords:
                # keyword_new = re.sub(r'/aplog.?/Boot\-', './logpa/Boot-', keyword, 1)
                output_line_target += keyword + "  "
            output_line_target += "\n"
            # output_lines.append(output_line_target)
            output_line_target_modified = re.sub(r'^.{12}', '/logpa/Boot-', output_line_target, 1)
            target_similar_lines_list.append(output_line_target_modified)
            ####print(output_line_target_modified)
            # print(output_line_target)
            if regexp_max == len(target_similar_lines_list):
                ####print("regexp_max == len(target_similar_lines_list)")
                break
    # if target_similar_lines_list len > 0,  insert the regexp_string to target_similar_lines_list, at first index:
    if len(target_similar_lines_list) > 0:
        target_similar_lines_list.insert(0, prefix_string*150 + regexp_string + "     " + str(regexp_max) + "\n")
    return target_similar_lines_list


if __name__ == '__main__':
    my_log("Finding same lines in two files ...", True)

    # check if the args, if the args are not right , exit
    # https://blog.csdn.net/liuyingying0418/article/details/100126348

    if len(sys.argv) == 4:
        source_file = sys.argv[1]
        target_file = sys.argv[2]
        output_file = sys.argv[3]
    if len(sys.argv) == 3:
        source_file = sys.argv[1]
        target_file = sys.argv[2]
        output_file = "output_" + source_file

    print(len(sys.argv))
    print(r'''let's \b\n go home''')
    print(r'hello world\\')
    find_lines_in_two_files(source_file, target_file, output_file)
    # try:
    #     find_lines_in_two_files(source_file, target_file, output_file)
    # except Exception as e:
    #     my_log('Exception ：\n%s' % e)
    #     print(e)
    #     sys.exit(1)
    my_log("Finding Finished! ")
    sys.exit(0)
