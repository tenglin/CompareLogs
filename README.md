# CompareLogs
This python script will help you find the difference between two logs. The finding process is based on the Regular Expressions.

If you are a system software engineer, sometimes you need to analyze some logs to find problems in the system you are developing, but if you are dealing with very large logs, finding the rootcause of the issues becomes very time consuming.
The purpose of this program is to make this process a little bit easier.

This program is designed in such a way: You need provide two logs, one log that runs normally and one log that does not run normally, and by comparing these two logs, you can find out where the errors may be occurring.

But because the log contains differences in time, process number, etc., simply comparing the two logs will give you a lot of differences. This doesn't help us much.

So, we configure the comparing by regular expressions and compare only the differences we are interested.
You can change the comparing configuration in the file config_find_lines.yaml.

This script in practice works well. But I need further explain on how to use it later. 
I will updated the usage instructions in the near future.

