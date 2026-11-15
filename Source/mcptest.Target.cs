// Game target. Exists so UE 5.9 Preview 1 can build the project for the web (Wasm needs a code project);
// the game itself is all Blueprints. See Docs/Web_网页版构建.md.

using UnrealBuildTool;
using System.Collections.Generic;

public class mcptestTarget : TargetRules
{
	public mcptestTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V8;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_9;
		ExtraModuleNames.Add("mcptest");
	}
}
