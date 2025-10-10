package org.healthnlp.annotation.labelstudio.result;

import org.healthnlp.annotation.labelstudio.result.value.ChoicesValue;
import org.healthnlp.annotation.labelstudio.result.value.LabelsValue;

import java.util.List;

public class LabelsResult extends Result {
    public LabelsResult(int start, int end, String text, List<String> labels){
        this("Event", "text", "manual", start, end, text, labels);
    }
    public LabelsResult(String from_name, String to_name, String origin, int start, int end, String text, List<String> labels){
        this.from_name = from_name;
        this.to_name = to_name;
        this.origin = origin;
        this.type = "labels";
        this.value = new LabelsValue(start, end, text, labels);
    }
}
