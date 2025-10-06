package org.healthnlp.annotation.labelstudio.result;

import org.healthnlp.annotation.labelstudio.result.value.TextAreaValue;

import java.util.List;

public class TextAreaResult extends Result {
    public TextAreaValue value;

    public TextAreaResult(int start, int end, List<String> text){
        // Maybe one day there will be a
        // more generalized way of dealing with
        // Label Studio from Java but for now
        // in the spirit of "getting things done"
        // just go with specious and expedient
        this("CUI", "text", "manual", start, end, text);
    }

    public TextAreaResult(String from_name, String to_name, String origin, int start, int end, List<String> text){
        this.from_name = from_name;
        this.to_name = to_name;
        this.origin = origin;
        this.type = "textarea";
        this.value = new TextAreaValue(start, end, text);
    }
}
