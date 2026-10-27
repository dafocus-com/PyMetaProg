// Copyright 2025-2026 Davide Achilli (DAFOCUS - https://www.dafocus.com)
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at:
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Author: Davide Achilli <davide.achilli@dafocus.com>
using System.IO;
using System.Text;

namespace MetaProg {


	/// <summary>
	/// Allows building a string with indented lines
	/// </summary>
	public class Indenter {
		/// <summary>
		/// Internal string builder that accumulates the string
		/// </summary>
		private StringBuilder stringBuilder = new StringBuilder();

		/// <summary>
		/// Current indent level
		/// </summary>
		private int indentLevel = 0;

		/// <summary>
		/// Keeps track if the previous write terminated with a newline
		/// </summary>
		private bool lastWasNewLine = true;

		/// <summary>
		/// Text used for indentation
		/// </summary>
		private string IndentText {get; set;} = "  " ;

		/// <summary>
		/// Increase the indent level
		/// </summary>
		/// <param name="indent">Number of indents to be added</param>
		public void IncIndent(int indent=1) {indentLevel += indent;}

		/// <summary>
		/// Decrease the indent level
		/// </summary>
		/// <param name="indent">Number of indents to be removed</param>
		public void DecIndent(int indent=1) {indentLevel -= indent;}

		/// <summary>
		/// Add multi-line text to the indented data
		/// </summary>
		/// <param name="text">The multi-line text</param>
		public void AddText(string text) {
			using var reader = new StringReader(text);
			string? line;
			bool isFirstLine = true;
			while ((line = reader.ReadLine()) != null)
			{
				if (isFirstLine) { isFirstLine=false; }
				else { stringBuilder.Append("\n");}
				if (lastWasNewLine) {
					for (int i = 0; i < indentLevel; i++)
					{
						stringBuilder.Append(IndentText);
					}
				}
				stringBuilder.Append(line);
				lastWasNewLine = true;
			}
			if (text.Length > 0) {
				lastWasNewLine = text.EndsWith("\n");
				if (lastWasNewLine) { stringBuilder.Append("\n");}
			}
		}

		/// <summary>
		/// Add a newline
		/// </summary>
		public void AddNewLine() {AddText("\n");}

		/// <summary>
		/// Return the text as a string
		/// </summary>
		/// <returns>The string</returns>
		public override string ToString() { return stringBuilder.ToString(); }

	}
}