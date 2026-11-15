// Editor target for the code project (see mcptest.Target.cs).

using UnrealBuildTool;
using System.Collections.Generic;

public class mcptestEditorTarget : TargetRules
{
	public mcptestEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.V8;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_9;
		ExtraModuleNames.Add("mcptest");
	}
}
