package org.healthnlp.annotation.labelstudio.result.value;

import java.util.List;

public class LabelsValue extends Value {
    public String text;
    public List<String> labels;

    public LabelsValue(int start, int end, String text, List<String> labels){
        super(start, end);
        this.text = text;
        this.labels = labels;
    }
}
