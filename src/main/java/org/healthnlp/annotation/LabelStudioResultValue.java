package org.healthnlp.annotation;

import java.util.LinkedList;
import java.util.List;

public class LabelStudioResultValue {
    public int start;
    public int end;
    public String text;
    public List<String> labels = new LinkedList<>();
}
