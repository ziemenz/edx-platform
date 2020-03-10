#!/usr/bin/env bash

while read -r app; do
	cat template.py | sed -e "s/TEMPLATE/${app}/g" > lms/"$app".py
done < lms_apps.lst
