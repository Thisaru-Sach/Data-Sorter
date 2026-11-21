"""Quick checks for the sorting logic. Run: python test_sorter.py"""
import pandas as pd
from sorter import SortRule, sort_dataframe, looks_like_date, detect_dayfirst, save_dataframe, load_csv, load_excel


def test_all():
    df = pd.DataFrame({
        "Name": ["bob", "Alice", "carl", "dave", None, "Eve"],
        "Dept": ["B", "A", "B", "A", "A", "B"],
        "Score": ["10", "9", "2", "100", "5", ""],
        "Joined": ["25/12/2024", "01/02/2024", "15/01/2025", "03/04/2024", "01/01/2024", "07/07/2024"],
    })
    assert looks_like_date(df["Joined"]) and not looks_like_date(df["Score"]) and not looks_like_date(df["Name"])
    assert detect_dayfirst(df["Joined"]) is True

    # numbers stored as text sort numerically, blanks last
    out = sort_dataframe(df, [SortRule("Score", True)])
    assert list(out["Score"][:5]) == ["2", "5", "9", "10", "100"] and out["Score"].iloc[-1] == ""
    # descending keeps blanks last
    out = sort_dataframe(df, [SortRule("Score", False)])
    assert out["Score"].iloc[0] == "100" and out["Score"].iloc[-1] == ""
    # dates sort as dates (day first), not as text
    out = sort_dataframe(df, [SortRule("Joined", True, as_date=True, dayfirst=True)])
    assert list(out["Joined"]) == ["01/01/2024", "01/02/2024", "03/04/2024", "07/07/2024", "25/12/2024", "15/01/2025"]
    # multi-column: Dept asc, then Score desc
    out = sort_dataframe(df, [SortRule("Dept", True), SortRule("Score", False)])
    assert list(out["Dept"]) == ["A", "A", "A", "B", "B", "B"]
    assert list(out["Score"][:3]) == ["100", "9", "5"]
    # case-insensitive text, column order untouched
    out = sort_dataframe(df, [SortRule("Name", True)])
    assert list(out["Name"][:4]) == ["Alice", "bob", "carl", "dave"] and pd.isna(out["Name"].iloc[-1])
    assert list(out.columns) == list(df.columns)

    # round trip through xlsx and csv
    import tempfile, os
    d = tempfile.mkdtemp()
    df2 = pd.DataFrame({"D": pd.to_datetime(["2024-03-01", "2024-01-05"]), "V": [2, 1]})
    save_dataframe(sort_dataframe(df2, [SortRule("D", True, as_date=True)]), os.path.join(d, "a.xlsx"))
    back = load_excel(os.path.join(d, "a.xlsx"), "Sorted")
    assert list(back.columns) == ["D", "V"] and back["V"].tolist() == [1, 2]
    save_dataframe(df, os.path.join(d, "a.csv"), ";")
    back, delim = load_csv(os.path.join(d, "a.csv"))
    assert delim == ";" and list(back.columns) == list(df.columns)
    print("All sorter tests passed")


if __name__ == "__main__":
    test_all()
