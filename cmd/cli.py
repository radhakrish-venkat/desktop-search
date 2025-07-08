import click

@click.group()
def cli():
    """Desktop Search CLI"""
    pass

@cli.command()
def version():
    """Show version information"""
    click.echo("Desktop Search v1.0.0")

if __name__ == '__main__':
    cli()