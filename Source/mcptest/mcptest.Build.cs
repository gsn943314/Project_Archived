// The project's only C++ module: a placeholder so the project counts as a code project
// (UE 5.9 Preview 1 builds web/Wasm games from code projects only). No gameplay code lives here.

using UnrealBuildTool;

public class mcptest : ModuleRules
{
	public mcptest(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
		// RenderCore + RHI: the web forward-tier check in mcptest.cpp
		PrivateDependencyModuleNames.AddRange(new string[] { "RenderCore", "RHI" });
	}
}
